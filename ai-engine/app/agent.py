from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import statistics

from openai import AsyncOpenAI, RateLimitError, AuthenticationError
from pydantic import ValidationError

from .db import get_pool
from .memory import save_memory, retrieve_memories
from .prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    build_combined_prompt,
    build_profile_block,
    build_platform_behavior,
    build_memory_block,
)
from .schemas import (
    AdMetrics,
    AdType,
    CognitiveLoopResult,
    Conclusion,
    FinalAction,
    PersonaInput,
    PersonaReactionSignal,
    SelfishFiltering,
    SimulationResponse,
    UnconsciousReaction,
)
from .vision import build_visual_ad_description

logger = logging.getLogger(__name__)

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
        # 모듈 로드 시점이 아닌 첫 호출 시점에 읽어야 load_dotenv() 이후 값이 보장됨
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

    # DPP(Deal Proneness): 높을수록 가격 자극에 감정적·즉각적으로 반응 → variability 증가
    # 낮을수록 가격보다 가치/품질로 판단 → 안정적 반응
    if persona.deal_prone_score is not None:
        temp += (persona.deal_prone_score - 0.5) * 0.20

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
    if result.step3_final_action.reasoning_chain:
        texts.append(result.step3_final_action.reasoning_chain)
    return any(_KOREAN_ONLY.search(t) for t in texts)


# ── 세그먼트 자동 계산 ────────────────────────────────────────────────────────

def _compute_segment(persona: PersonaInput) -> str:
    decade = f"{(persona.age // 10) * 10}s"
    if persona.gender:
        g = persona.gender.lower()
        if "여" in g or "female" in g:
            return f"{decade}_female"
        if "남" in g or "male" in g:
            return f"{decade}_male"
    return decade


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
        persona_name=persona.name,
        persona_age=persona.age,
        persona_job=persona.job,
        segment=_compute_segment(persona),
        attention=attention,
        sentiment=step2.sentiment,
        click_intent=step3.clicked,
        conversion_intent=step3.conversion_intent,
        comprehension=step2.comprehension,
        reasoning=step2.reason,
        recall=step2.recall,
        emotions=step1.emotions,
        confidence=_calibrate_confidence(step3.confidence, persona, step1.appeal_score),
        impression=step3.impression,
        reasoning_chain=step3.reasoning_chain,
    )


# ── IQR 이상치 감지 (여태호 요구사항 §11.1 전략 5) ────────────────────────────

def _filter_outliers(
    signals: list[PersonaReactionSignal],
) -> tuple[list[PersonaReactionSignal], int]:
    if len(signals) < 10:
        return signals, 0

    scores = sorted(s.attention for s in signals)
    qs = statistics.quantiles(scores, n=4)
    q1, q3 = qs[0], qs[2]
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


# ── OpenAI 호출 헬퍼 ──────────────────────────────────────────────────────────

async def _call_openai(system: str, user: str, temperature: float = _BASE_TEMPERATURE) -> str:
    async with _get_semaphore():
        response = await _get_client().chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
    return response.choices[0].message.content


async def _call_openai_text(system: str, user: str, temperature: float = _BASE_TEMPERATURE) -> str:
    """JSON 형식 없이 텍스트 응답을 반환하는 헬퍼 (Reflection 생성 등에 사용)"""
    async with _get_semaphore():
        response = await _get_client().chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=150,
        )
    return response.choices[0].message.content.strip()


# ── Paper 3: Confidence 보정 ──────────────────────────────────────────────────

def _calibrate_confidence(raw: float | None, persona: PersonaInput, appeal_score: int) -> float | None:
    """페르소나 특성 기반 신뢰도 사후 보정 (Paper 3 — Agentic Confidence Calibration)"""
    if raw is None:
        return None
    c = raw
    if persona.brand_loyalty is not None and persona.brand_loyalty < 0.3:
        c *= 0.85  # 브랜드 신뢰 낮음 → 확신 감소
    if persona.age > 55:
        c *= 0.90  # 보수적 연령대 → 확신 감소
    if appeal_score == 5:
        c = min(c * 1.10, 1.0)  # 강한 본능 반응 → 확신 증폭
    if persona.deal_prone_score is not None and persona.deal_prone_score >= 0.7 and appeal_score >= 4:
        c = min(c * 1.05, 1.0)  # 가격 민감 + 높은 관심 → 확신 소폭 증폭
    return round(min(max(c, 0.0), 1.0), 3)


# ── Paper 1: Memory Importance 점수 계산 ─────────────────────────────────────

def _compute_importance(signal: PersonaReactionSignal) -> int:
    """광고 반응 중요도 1-10 점수 (Paper 1 — Generative Agents)"""
    if signal.conversion_intent:
        return 9  # 구매 의향 → 가장 중요한 기억
    if signal.click_intent:
        return 7  # 클릭 → 중요
    if signal.sentiment <= -0.5:
        return 4  # 강한 거부 → 부정 패턴으로서 의미 있음
    if signal.sentiment >= 0.5:
        return 6  # 호감이었지만 클릭 미발생
    return 3  # 스크롤 넘김 → 낮은 중요도


# ── 메모리 이벤트 내용 생성 ───────────────────────────────────────────────────

def _build_event_content(signal: PersonaReactionSignal, ad_content: str) -> tuple[str, str]:
    ad_hint = ad_content[:80].replace("\n", " ")

    parts = [f"광고 노출: {ad_hint}"]
    if signal.emotions:
        parts.append(f"즉각 감정: {', '.join(signal.emotions)}")
    if signal.impression:
        parts.append(f"인상: {signal.impression}")

    if signal.conversion_intent:
        parts.append("행동: 클릭 후 구매 의향 있음")
        tag = "PURCHASE"
    elif signal.click_intent:
        parts.append("행동: 클릭함 (구매 의향 없음)")
        tag = "EVENT"
    else:
        parts.append("행동: 스크롤로 넘김")
        tag = "EVENT"

    return " | ".join(parts), tag


# ── 단일 페르소나 시뮬레이션 (3단계 체인 + Step 2.5) ─────────────────────────

async def _simulate_one(
    persona: PersonaInput,
    ad_content: str,
    objective: str,
    product_price: int | None,
    ad_id: str = "",
    attempt: int = 0,
    memories: list[dict] | None = None,
) -> PersonaReactionSignal | None:
    temperature = _assign_temperature(persona)
    memory_block = build_memory_block(memories or [])

    system = SYSTEM_PROMPT_TEMPLATE.format(
        name=persona.name,
        age=persona.age,
        gender=persona.gender or "미지정",
        job=persona.job,
        emotional_state=persona.emotional_state or "보통",
        platform=persona.platform or "스마트폰",
        platform_behavior=build_platform_behavior(persona.platform),
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        profile_block=build_profile_block(persona),
        memory_block=memory_block,
    )
    prompt = build_combined_prompt(
        ad_content=ad_content,
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        objective=objective,
        product_price=product_price,
        price_threshold=persona.price_threshold,
        deal_prone_score=persona.deal_prone_score,
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
            reasoning_chain=data.get("reasoning_chain"),
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
                return await _simulate_one(persona, ad_content, objective, product_price, ad_id, attempt + 1, memories)
            logger.error("Persona %s — 재시도 후에도 비한국어 응답", persona.persona_id)

        return _to_signal(internal, persona, ad_id, objective)

    except (KeyError, json.JSONDecodeError, ValidationError) as exc:
        if attempt < MAX_RETRIES:
            logger.warning(
                "Persona %s — JSON 파싱/검증 실패, 재시도 (attempt %d): %s",
                persona.persona_id, attempt + 1, exc,
            )
            await asyncio.sleep(1)
            return await _simulate_one(persona, ad_content, objective, product_price, ad_id, attempt + 1, memories)
        logger.error("Persona %s — JSON 파싱/검증 영구 실패: %s", persona.persona_id, exc)
        return None

    except RateLimitError:
        if attempt >= MAX_RETRIES:
            logger.error("Persona %s — rate limit 재시도 초과", persona.persona_id)
            return None
        wait = 2 ** attempt * 5
        logger.warning("Persona %s — rate limit, %ds 대기 (attempt %d)", persona.persona_id, wait, attempt + 1)
        await asyncio.sleep(wait)
        return await _simulate_one(persona, ad_content, objective, product_price, ad_id, attempt + 1, memories)

    except AuthenticationError:
        logger.error("Persona %s — OpenAI 인증 오류: OPENAI_API_KEY 확인", persona.persona_id)
        return None

    except Exception as exc:
        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            logger.warning("Retrying persona %s (attempt %d): %s", persona.persona_id, attempt + 1, exc)
            await asyncio.sleep(wait)
            return await _simulate_one(persona, ad_content, objective, product_price, ad_id, attempt + 1, memories)
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

    # 페르소나별 관련 메모리 병렬 조회
    pool = get_pool()
    memory_results = await asyncio.gather(
        *[retrieve_memories(pool, p.persona_id, ad_content) for p in personas],
        return_exceptions=True,
    )
    memories_per_persona: list[list[dict]] = [
        m if isinstance(m, list) else [] for m in memory_results
    ]

    logger.info("ad_id=%s | 전체 %d 페르소나 병렬 실행", ad_id, len(personas))
    gather_results = await asyncio.gather(
        *[
            _simulate_one(p, ad_content, objective, product_price, ad_id, memories=mem)
            for p, mem in zip(personas, memories_per_persona)
        ],
        return_exceptions=True,
    )
    raw_signals = [s for s in gather_results if isinstance(s, PersonaReactionSignal)]

    if not raw_signals:
        raise RuntimeError("All persona simulations failed — check OPENAI_API_KEY/quota")

    # 시뮬레이션 결과를 메모리에 비동기 저장 (실패해도 시뮬레이션 결과에 영향 없음)
    if pool:
        asyncio.ensure_future(
            _save_simulation_memories(pool, raw_signals, personas, ad_content)
        )

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

    metrics = _calc_metrics(clean_signals, outlier_count)
    conclusion = await _generate_conclusion(metrics, clean_signals, objective)

    return SimulationResponse(
        ad_id=ad_id,
        total_personas=len(clean_signals),
        results=clean_signals,
        metrics=metrics,
        conclusion=conclusion,
    )


async def _maybe_generate_reflection(pool, persona_id: str, persona_name: str) -> None:
    """5의 배수 이벤트 도달 시 Reflection 메모리 합성 (Paper 1 — Generative Agents)"""
    try:
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM persona_memories WHERE persona_id = $1 AND tag != 'REFLECTION'",
                persona_id,
            )
        if count == 0 or count % 5 != 0:
            return

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT content FROM persona_memories"
                " WHERE persona_id = $1 AND tag != 'REFLECTION'"
                " ORDER BY created_at DESC LIMIT 5",
                persona_id,
            )
        memories_text = "\n".join(f"- {r['content']}" for r in rows)

        system = (
            "당신은 소비자 행동 분석 전문가입니다. "
            "아래 광고 반응 이력을 보고 이 사람의 광고 소비 패턴을 한 문장으로 요약하세요. "
            "분석적 언어 없이 사실만 기술하세요. 한국어로만 답하세요."
        )
        prompt = (
            f"[{persona_name}의 최근 광고 반응 이력]\n{memories_text}\n\n"
            "→ 이 사람의 광고 소비 패턴 (한 문장):"
        )

        reflection = await _call_openai_text(system, prompt, temperature=0.3)
        await save_memory(pool, persona_id, "REFLECTION", reflection, importance=8)
        logger.info("Reflection 생성: persona=%s count=%d", persona_id, count)
    except Exception as exc:
        logger.warning("Reflection 생성 실패 (persona=%s): %s", persona_id, exc)


async def _save_simulation_memories(
    pool,
    signals: list[PersonaReactionSignal],
    personas: list[PersonaInput],
    ad_content: str,
) -> None:
    persona_map = {p.persona_id: p for p in personas}
    tasks = []
    for signal in signals:
        content, tag = _build_event_content(signal, ad_content)
        importance = _compute_importance(signal)
        tasks.append(save_memory(pool, signal.persona_id, tag, content, importance))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        logger.warning("메모리 저장 실패 %d건: %s", len(errors), errors[0])

    # Paper 1: 5의 배수 도달 시 Reflection 생성 (fire-and-forget)
    for signal in signals:
        persona = persona_map.get(signal.persona_id)
        if persona:
            asyncio.ensure_future(
                _maybe_generate_reflection(pool, signal.persona_id, persona.name)
            )


# ── 집계 지표 ─────────────────────────────────────────────────────────────────

def _calc_metrics(signals: list[PersonaReactionSignal], outlier_count: int = 0) -> AdMetrics:
    n = len(signals)

    # appeal_score는 더 이상 직접 갖고 있지 않음 — attention으로부터 역산
    # attention = (appeal_score - 1) / 4  →  appeal_score = attention * 4 + 1
    avg_attention = sum(s.attention for s in signals) / n
    avg_appeal = round(avg_attention * 4 + 1, 2)

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


async def _generate_conclusion(
    metrics: AdMetrics,
    signals: list[PersonaReactionSignal],
    objective: str,
) -> Conclusion | None:
    impressions = [s.impression for s in signals if s.impression][:6]
    impressions_block = "\n".join(f"- {imp}" for imp in impressions)

    system = (
        "당신은 광고 성과 분석 전문가입니다. "
        "시뮬레이션 결과를 바탕으로 광고 집행 여부에 대한 명확한 결론을 JSON으로 작성하세요.\n\n"
        "반환 형식:\n"
        "{\n"
        '  "verdict": "집행 권장" | "수정 후 재검토" | "집행 비권장",\n'
        '  "reason": "2~3문장으로 판단 근거 설명",\n'
        '  "strengths": ["강점1", "강점2"],\n'
        '  "weaknesses": ["약점1", "약점2"]\n'
        "}\n"
        "모든 텍스트는 한국어로 작성하세요."
    )

    prompt = (
        f"다음 광고 시뮬레이션 결과를 분석하고 집행 여부를 판단하세요.\n\n"
        f"[성과 지표]\n"
        f"VTR(조회완료율): {metrics.vtr}%\n"
        f"CTR(클릭률): {metrics.ctr}%\n"
        f"CVR(전환율): {metrics.cvr}%\n"
        f"이탈률: {metrics.dropout_rate}%\n"
        f"매력도: {metrics.avg_appeal_score}/5\n"
        f"평균 감정: {metrics.avg_sentiment:.2f} (-1=강한거부 ~ 1=강한호감)\n"
        f"캠페인 목적: {objective}\n\n"
        f"[페르소나 인상 샘플]\n{impressions_block}\n\n"
        "집행 기준:\n"
        "- 집행 권장: VTR≥35% 또는 CTR≥3% 또는 매력도≥4.0\n"
        "- 집행 비권장: VTR<25% 이고 CTR<1.5% 이고 이탈률≥70%\n"
        "- 그 외: 수정 후 재검토"
    )

    try:
        raw = await _call_openai(system, prompt, temperature=0.3)
        data = json.loads(raw)
        return Conclusion(
            verdict=data["verdict"],
            reason=data["reason"],
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
        )
    except Exception as exc:
        logger.warning("결론 생성 실패: %s", exc)
        return None
