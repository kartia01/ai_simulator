from __future__ import annotations

import asyncio
import json
import logging
import os
import re

from openai import AsyncOpenAI, RateLimitError, AuthenticationError

from .prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    build_combined_prompt,
    build_profile_block,
    build_platform_behavior,
    build_filter_type,
)
from .schemas import (
    AdMetrics,
    AdType,
    CognitiveLoopResult,
    FinalAction,
    PersonaInput,
    PersonaReactionSignal,
    SelfishFiltering,
    SimulationResponse,
    UnconsciousReaction,
)
from .vision import build_visual_ad_description

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("OPENAI_API_KEY")
_MODEL = "gpt-4o-mini"

MAX_RETRIES = 3
_BASE_TEMPERATURE = 0.70

_KOREAN_ONLY = re.compile(r"[^가-힣ᄀ-ᇿ㄰-㆏0-9\s\.,!?~\-\"\'%/·…]")

_client: AsyncOpenAI | None = None
_semaphore: asyncio.Semaphore | None = None

_SEMAPHORE_LIMIT = 15


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=_API_KEY)
    return _client


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(_SEMAPHORE_LIMIT)
    return _semaphore


# ── 페르소나별 temperature 동적 할당 (여태호 요구사항 §6.3 메커니즘 1) ───────────

def _assign_temperature(persona: PersonaInput) -> float:
    temp = _BASE_TEMPERATURE

    # 충동 구매 성향 → 높은 variability
    if persona.purchase_pattern and "충동" in persona.purchase_pattern:
        temp += 0.15

    # 브랜드 충성도 낮을수록 → 더 가변적 반응
    if persona.brand_loyalty is not None:
        temp += (1.0 - persona.brand_loyalty) * 0.10

    # 연령: 50대 이상 → 보수적, 30세 미만 → 충동적
    if persona.age > 50:
        temp -= 0.10
    elif persona.age < 30:
        temp += 0.10

    return round(min(max(temp, 0.50), 1.10), 2)


# ── 논리 모순 보정 ─────────────────────────────────────────────────────────────

def _fix_logic_errors(result: CognitiveLoopResult, objective: str = "conversion") -> CognitiveLoopResult:
    step1 = result.step1_unconscious_reaction
    step2 = result.step2_selfish_filtering
    step3 = result.step3_final_action

    # 점수 최저인데 이탈 안 함
    if step1.appeal_score == 1 and not step2.is_dropped_out:
        logger.warning("Persona %s — 점수=1인데 이탈=False → 이탈 True 보정", result.persona_id)
        step2.is_dropped_out = True
        step3.clicked = False
        step3.conversion_intent = False
        step3.action_reason = "눈길도 안 갔다"

    # 이탈했는데 클릭 True
    if step2.is_dropped_out and step3.clicked:
        logger.warning("Persona %s — 이탈=True·클릭=True → 클릭 False 보정", result.persona_id)
        step3.clicked = False
        step3.conversion_intent = False
        step3.action_reason = "그냥 넘겼다"

    # 점수 낮은데 클릭 True
    if step1.appeal_score <= 2 and step3.clicked:
        logger.warning("Persona %s — 점수≤2인데 클릭=True → 클릭 False 보정", result.persona_id)
        step3.clicked = False
        step3.conversion_intent = False
        step3.action_reason = "별로였다"

    # 이탈했는데 전환 의향 True (modify.md §4-2)
    if step2.is_dropped_out and step3.conversion_intent:
        step3.conversion_intent = False

    # 클릭 없이 전환 의향 True
    if not step3.clicked and step3.conversion_intent:
        step3.conversion_intent = False

    # awareness 캠페인은 전환 의향 항상 False
    if objective == "awareness":
        step3.conversion_intent = False

    return result


# ── 비한국어 감지 ──────────────────────────────────────────────────────────────

def _has_foreign_text(result: CognitiveLoopResult) -> bool:
    texts = [
        *result.step1_unconscious_reaction.emotions,
        result.step2_selfish_filtering.reason,
        result.step3_final_action.action_reason,
        result.step3_final_action.impression,
    ]
    return any(_KOREAN_ONLY.search(t) for t in texts)


# ── CognitiveLoopResult → PersonaReactionSignal 변환 ─────────────────────────

def _to_signal(
    internal: CognitiveLoopResult,
    persona: PersonaInput,
    ad_id: str,
    objective: str,
) -> PersonaReactionSignal:
    step1 = internal.step1_unconscious_reaction
    step2 = internal.step2_selfish_filtering
    step3 = internal.step3_final_action

    # appeal_score(1-5) → attention(0.0-1.0) 선형 변환 (modify.md §4-3)
    attention = round((step1.appeal_score - 1) / 4, 3)

    return PersonaReactionSignal(
        creative_id=ad_id,
        objective=objective,
        persona_id=persona.persona_id,
        segment=persona.segment or "unknown",
        attention=attention,
        sentiment=step2.sentiment,
        click_intent=step3.clicked,
        conversion_intent=step3.conversion_intent,
        comprehension=step2.comprehension,
        reasoning=step2.reason,
        recall=step2.recall,
        emotions=step1.emotions,
        confidence=step3.confidence,
        impression=step3.impression,
    )


# ── IQR 이상치 감지 (여태호 요구사항 §11.1 전략 5) ────────────────────────────

def _filter_outliers(
    signals: list[PersonaReactionSignal],
) -> tuple[list[PersonaReactionSignal], int]:
    if len(signals) < 10:
        return signals, 0

    scores = sorted(s.attention for s in signals)
    n = len(scores)
    q1 = scores[n // 4]
    q3 = scores[(3 * n) // 4]
    iqr = q3 - q1

    # IQR가 0이면 (모든 점수 동일) 필터 생략
    if iqr == 0:
        return signals, 0

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    clean = [s for s in signals if lower <= s.attention <= upper]
    removed = len(signals) - len(clean)

    if removed:
        logger.info("IQR 이상치 %d개 제외 (attention 범위: %.3f~%.3f)", removed, lower, upper)

    return clean, removed


# ── OpenAI 단일 호출 헬퍼 ──────────────────────────────────────────────────────

async def _call_openai(system: str, user: str, temperature: float = _BASE_TEMPERATURE) -> str:
    async with _get_semaphore():
        response = await _get_client().chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
    return response.choices[0].message.content


# ── 단일 페르소나 시뮬레이션 (3단계 체인) ─────────────────────────────────────

async def _simulate_one(
    persona: PersonaInput,
    ad_content: str,
    objective: str,
    product_price: int | None,
    attempt: int = 0,
) -> PersonaReactionSignal | None:
    temperature = _assign_temperature(persona)

    system = SYSTEM_PROMPT_TEMPLATE.format(
        name=persona.name,
        age=persona.age,
        job=persona.job,
        emotional_state=persona.emotional_state or "보통",
        platform=persona.platform or "스마트폰",
        platform_behavior=build_platform_behavior(persona.platform),
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        filter_type=build_filter_type(persona.mbti),
        profile_block=build_profile_block(persona),
    )
    prompt = build_combined_prompt(
        ad_content=ad_content,
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        objective=objective,
        product_price=product_price,
        price_threshold=persona.price_threshold,
    )

    try:
        raw = await _call_openai(system, prompt, temperature=temperature)
        data = json.loads(raw)

        step1 = UnconsciousReaction(
            emotions=data["emotions"],
            appeal_score=data["appeal_score"],
        )
        step2 = SelfishFiltering(
            is_dropped_out=data["is_dropped_out"],
            reason=data["reason"],
            sentiment=data["sentiment"],
            comprehension=data["comprehension"],
            recall=data["recall"],
        )
        step3 = FinalAction(
            clicked=data["clicked"],
            conversion_intent=data["conversion_intent"],
            action_reason=data["action_reason"],
            impression=data["impression"],
            confidence=data["confidence"],
        )

        internal = _fix_logic_errors(
            CognitiveLoopResult(
                persona_id=persona.persona_id,
                step1_unconscious_reaction=step1,
                step2_selfish_filtering=step2,
                step3_final_action=step3,
            ),
            objective=objective,
        )

        if _has_foreign_text(internal):
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Persona %s — 비한국어 감지, 재시도 (attempt %d)",
                    persona.persona_id, attempt + 1,
                )
                await asyncio.sleep(1)
                return await _simulate_one(persona, ad_content, objective, product_price, attempt + 1)
            logger.error("Persona %s — 재시도 후에도 비한국어 응답", persona.persona_id)

        return _to_signal(internal, persona, "pending", objective)

    except RateLimitError:
        if attempt >= MAX_RETRIES:
            logger.error("Persona %s — rate limit 재시도 초과", persona.persona_id)
            return None
        wait = 2 ** attempt * 5
        logger.warning("Persona %s — rate limit, %ds 대기 (attempt %d)", persona.persona_id, wait, attempt + 1)
        await asyncio.sleep(wait)
        return await _simulate_one(persona, ad_content, objective, product_price, attempt + 1)

    except AuthenticationError:
        logger.error("Persona %s — OpenAI 인증 오류: OPENAI_API_KEY 확인", persona.persona_id)
        return None

    except Exception as exc:
        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            logger.warning("Retrying persona %s (attempt %d): %s", persona.persona_id, attempt + 1, exc)
            await asyncio.sleep(wait)
            return await _simulate_one(persona, ad_content, objective, product_price, attempt + 1)
        logger.error("Persona %s failed permanently: %s", persona.persona_id, exc, exc_info=True)
        return None


# ── Cascade pipeline ───────────────────────────────────────────────────────────

async def run_cascade_simulation(
    personas: list[PersonaInput],
    ad_content: str,
    ad_id: str,
    ad_type: AdType = AdType.IMAGE,
    objective: str = "conversion",
    product_price: int | None = None,
    image_base64: str | None = None,
    video_base64: str | None = None,
    media_content_type: str | None = None,
) -> SimulationResponse:
    logger.info("ad_id=%s | ad_type=%s | objective=%s | personas=%d", ad_id, ad_type, objective, len(personas))

    if image_base64 or video_base64:
        logger.info("ad_id=%s | 미디어 비전 분석 시작", ad_id)
        ad_content = await build_visual_ad_description(
            ad_content=ad_content,
            image_base64=image_base64,
            video_base64=video_base64,
            media_content_type=media_content_type,
        )
        logger.info("ad_id=%s | 비전 분석 완료 (%d chars)", ad_id, len(ad_content))

    logger.info("ad_id=%s | 전체 %d 페르소나 병렬 실행", ad_id, len(personas))
    raw_signals = [
        s for s in await asyncio.gather(*[
            _simulate_one(p, ad_content, objective, product_price) for p in personas
        ])
        if s is not None
    ]

    if not raw_signals:
        raise RuntimeError("All persona simulations failed — check OPENAI_API_KEY/quota")

    # creative_id를 실제 ad_id로 채움 (_simulate_one에서 "pending"으로 임시 설정)
    for sig in raw_signals:
        sig.creative_id = ad_id

    # IQR 이상치 감지 및 제거 (여태호 요구사항 §11.1 전략 5)
    clean_signals, outlier_count = _filter_outliers(raw_signals)

    if not clean_signals:
        logger.warning("IQR 필터 후 유효 응답 없음 — 원본 사용")
        clean_signals = raw_signals
        outlier_count = 0

    logger.info(
        "ad_id=%s | 완료: %d/%d 성공 (이상치 %d개 제외)",
        ad_id, len(clean_signals), len(personas), outlier_count,
    )

    return SimulationResponse(
        ad_id=ad_id,
        total_personas=len(clean_signals),
        results=clean_signals,
        metrics=_calc_metrics(clean_signals, outlier_count),
    )


# ── 집계 지표 ─────────────────────────────────────────────────────────────────

def _calc_metrics(signals: list[PersonaReactionSignal], outlier_count: int = 0) -> AdMetrics:
    n = len(signals)

    # appeal_score는 더 이상 직접 갖고 있지 않음 — attention으로부터 역산
    # attention = (appeal_score - 1) / 4  →  appeal_score = attention * 4 + 1
    avg_attention = sum(s.attention for s in signals) / n
    avg_appeal = round(avg_attention * 4 + 1, 2)

    dropped = sum(1 for s in signals if not s.click_intent and s.attention < 0.5)
    # VTR: 이탈하지 않은 비율 (sentiment >= 0 또는 click_intent=True)
    stayed = sum(1 for s in signals if s.click_intent or s.sentiment >= 0)
    clicked = sum(1 for s in signals if s.click_intent)
    converted = sum(1 for s in signals if s.conversion_intent)
    avg_sentiment = sum(s.sentiment for s in signals) / n

    # dropout_rate: click_intent=False이고 sentiment < 0인 비율
    dropout = sum(1 for s in signals if not s.click_intent and s.sentiment < 0)

    return AdMetrics(
        vtr=round(stayed / n * 100, 1),
        ctr=round(clicked / n * 100, 1),
        cvr=round(converted / n * 100, 1),
        dropout_rate=round(dropout / n * 100, 1),
        avg_appeal_score=avg_appeal,
        avg_attention=round(avg_attention, 3),
        avg_sentiment=round(avg_sentiment, 3),
        outlier_count=outlier_count,
    )
