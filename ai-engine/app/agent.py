from __future__ import annotations

import asyncio
import json
import logging
import os
import re

# from groq import AsyncGroq, RateLimitError, AuthenticationError
from openai import AsyncOpenAI, RateLimitError, AuthenticationError

from .prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    STEP1_USER_PROMPT,
    STEP2_USER_PROMPT,
    STEP3_USER_PROMPT,
    _STEP3_DROPPED,
    _STEP3_STAYED,
    build_profile_block,
    build_platform_behavior,
)
from .schemas import (
    AdMetrics,
    AdType,
    CognitiveLoopResult,
    FinalAction,
    PersonaInput,
    SelfishFiltering,
    SimulationResponse,
    UnconsciousReaction,
)
from .vision import build_visual_ad_description

logger = logging.getLogger(__name__)

# _API_KEY = os.getenv("GROQ_API_KEY")
_API_KEY = os.getenv("OPENAI_API_KEY")
# _MODEL = "llama-3.3-70b-versatile"
_MODEL = "gpt-4o-mini"

MAX_RETRIES = 3
SCREENING_COUNT = 3
_TEMPERATURE = 0.60

# 허용 문자: 한글, 숫자, 공백, 한국어 문장부호
_KOREAN_ONLY = re.compile(r"[^가-힣ᄀ-ᇿ㄰-㆏0-9\s\.,!?~\-\"\'%/·…]")

# _client: AsyncGroq | None = None
_client: AsyncOpenAI | None = None


# def _get_client() -> AsyncGroq:
def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        # _client = AsyncGroq(api_key=_API_KEY)
        _client = AsyncOpenAI(api_key=_API_KEY)
    return _client


def _fix_logic_errors(result: CognitiveLoopResult) -> CognitiveLoopResult:
    """단계 간 논리 모순을 보정한다."""
    step1 = result.step1_unconscious_reaction
    step2 = result.step2_selfish_filtering
    step3 = result.step3_final_action

    # 점수 최저(1)인데 이탈 안 함
    if step1.appeal_score == 1 and not step2.is_dropped_out:
        logger.warning("Persona %s — 점수=1인데 이탈=False 모순 → 이탈 True 보정", result.persona_id)
        step2.is_dropped_out = True
        step3.clicked = False
        step3.action_reason = "눈길도 안 갔다"

    # 이탈했는데 클릭 True
    if step2.is_dropped_out and step3.clicked:
        logger.warning("Persona %s — 이탈=True·클릭=True 모순 → 클릭 False 보정", result.persona_id)
        step3.clicked = False
        step3.action_reason = "그냥 넘겼다"

    # 점수 낮은데 클릭 True
    if step1.appeal_score <= 2 and step3.clicked:
        logger.warning("Persona %s — 점수≤2인데 클릭=True 모순 → 클릭 False 보정", result.persona_id)
        step3.clicked = False
        step3.action_reason = "별로였다"

    return result


def _has_foreign_text(result: CognitiveLoopResult) -> bool:
    texts = [
        *result.step1_unconscious_reaction.keywords,
        result.step2_selfish_filtering.reason,
        result.step3_final_action.action_reason,
    ]
    return any(_KOREAN_ONLY.search(t) for t in texts)


# ── OpenAI 단일 호출 헬퍼 ──────────────────────────────────────────────────────

# async def _call_groq(system: str, user: str) -> str:
async def _call_openai(system: str, user: str) -> str:
    response = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=_TEMPERATURE,
        max_tokens=200,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ── Single persona (3단계 체인 호출) ──────────────────────────────────────────

async def _simulate_one(
    persona: PersonaInput,
    ad_content: str,
    attempt: int = 0,
) -> CognitiveLoopResult | None:
    system = SYSTEM_PROMPT_TEMPLATE.format(
        name=persona.name,
        age=persona.age,
        job=persona.job,
        emotional_state=persona.emotional_state or "보통",
        platform=persona.platform or "스마트폰",
        platform_behavior=build_platform_behavior(persona.platform),
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        profile_block=build_profile_block(persona),
    )

    try:
        # Step 1 — 1.5초 본능 반응
        step1_raw = await _call_openai(
            system,
            STEP1_USER_PROMPT.format(ad_content=ad_content),
        )
        step1 = UnconsciousReaction(**json.loads(step1_raw))

        # Step 2 — Step 1 결과를 받아 자기중심 필터링
        step2_raw = await _call_openai(
            system,
            STEP2_USER_PROMPT.format(
                keywords=", ".join(step1.keywords),
                appeal_score=step1.appeal_score,
                context=persona.context,
                drop_off_trigger=persona.drop_off_trigger,
            ),
        )
        step2 = SelfishFiltering(**json.loads(step2_raw))

        # Step 3 — Step 1+2 결과를 받아 최종 결정
        step3_raw = await _call_openai(
            system,
            STEP3_USER_PROMPT.format(
                keywords=", ".join(step1.keywords),
                appeal_score=step1.appeal_score,
                is_dropped_out=step2.is_dropped_out,
                reason=step2.reason,
                dropout_instruction=_STEP3_DROPPED if step2.is_dropped_out else _STEP3_STAYED,
            ),
        )
        step3 = FinalAction(**json.loads(step3_raw))

        result = _fix_logic_errors(CognitiveLoopResult(
            persona_id=persona.persona_id,
            step1_unconscious_reaction=step1,
            step2_selfish_filtering=step2,
            step3_final_action=step3,
        ))

        if _has_foreign_text(result):
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Persona %s — 비한국어 감지, 재시도 (attempt %d)",
                    persona.persona_id, attempt + 1,
                )
                await asyncio.sleep(1)
                return await _simulate_one(persona, ad_content, attempt + 1)
            logger.error("Persona %s — 재시도 후에도 비한국어 응답", persona.persona_id)

        return result

    except RateLimitError:
        if attempt >= MAX_RETRIES:
            logger.error("Persona %s — gave up after rate limit retries", persona.persona_id)
            return None
        wait = 2 ** attempt * 5
        logger.warning(
            "Persona %s — rate limit, waiting %ds (attempt %d)",
            persona.persona_id, wait, attempt + 1,
        )
        await asyncio.sleep(wait)
        return await _simulate_one(persona, ad_content, attempt + 1)

    except AuthenticationError:
        logger.error("Persona %s — OpenAI auth error: check OPENAI_API_KEY", persona.persona_id)
        return None

    except Exception as exc:
        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            logger.warning(
                "Retrying persona %s (attempt %d): %s",
                persona.persona_id, attempt + 1, exc,
            )
            await asyncio.sleep(wait)
            return await _simulate_one(persona, ad_content, attempt + 1)
        logger.error("Persona %s failed permanently: %s", persona.persona_id, exc, exc_info=True)
        return None


# ── Cascade pipeline ───────────────────────────────────────────────────────────

async def run_cascade_simulation(
    personas: list[PersonaInput],
    ad_content: str,
    ad_id: str,
    ad_type: AdType = AdType.IMAGE,
    image_base64: str | None = None,
    video_base64: str | None = None,
    media_content_type: str | None = None,
) -> SimulationResponse:
    logger.info("ad_id=%s | ad_type=%s | personas=%d", ad_id, ad_type, len(personas))

    if image_base64 or video_base64:
        logger.info("ad_id=%s | Analyzing media with vision model…", ad_id)
        ad_content = await build_visual_ad_description(
            ad_content=ad_content,
            image_base64=image_base64,
            video_base64=video_base64,
            media_content_type=media_content_type,
        )
        logger.info("ad_id=%s | Visual description ready (%d chars)", ad_id, len(ad_content))

    screening = personas[:SCREENING_COUNT]
    remainder = personas[SCREENING_COUNT:]

    logger.info("ad_id=%s | Stage-1 screening: %d personas", ad_id, len(screening))
    stage1 = list(await asyncio.gather(*[_simulate_one(p, ad_content) for p in screening]))

    stage2: list[CognitiveLoopResult | None] = []
    if remainder:
        logger.info("ad_id=%s | Stage-2 full batch: %d personas", ad_id, len(remainder))
        stage2 = await asyncio.gather(*[_simulate_one(p, ad_content) for p in remainder])

    all_results = [r for r in (*stage1, *stage2) if r is not None]

    if not all_results:
        raise RuntimeError("All persona simulations failed — check OPENAI_API_KEY/quota")

    logger.info(
        "ad_id=%s | Complete: %d/%d succeeded", ad_id, len(all_results), len(personas)
    )

    return SimulationResponse(
        ad_id=ad_id,
        total_personas=len(all_results),
        results=all_results,
        metrics=_calc_metrics(all_results),
    )


# ── Metrics ────────────────────────────────────────────────────────────────────

def _calc_metrics(results: list[CognitiveLoopResult]) -> AdMetrics:
    n = len(results)
    dropped = sum(1 for r in results if r.step2_selfish_filtering.is_dropped_out)
    clicked = sum(
        1 for r in results
        if r.step3_final_action.clicked
        and not r.step2_selfish_filtering.is_dropped_out
    )
    avg_appeal = sum(r.step1_unconscious_reaction.appeal_score for r in results) / n

    return AdMetrics(
        vtr=round((n - dropped) / n * 100, 1),
        ctr=round(clicked / n * 100, 1),
        dropout_rate=round(dropped / n * 100, 1),
        avg_appeal_score=round(avg_appeal, 2),
    )
