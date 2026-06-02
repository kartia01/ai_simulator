from __future__ import annotations

import asyncio
import json
import logging
import os
import re

from groq import AsyncGroq, RateLimitError, AuthenticationError

from .prompts import SYSTEM_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE, build_optional_profile
from .schemas import (
    AdMetrics,
    AdType,
    CognitiveLoopResult,
    PersonaInput,
    SimulationResponse,
)
from .vision import build_visual_ad_description

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("GROQ_API_KEY")
_MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 3
SCREENING_COUNT = 3
_TEMPERATURE = 0.60

# 허용 문자: 한글, 숫자, 공백, 한국어 문장부호
_KOREAN_ONLY = re.compile(r"[^가-힣ᄀ-ᇿ㄰-㆏0-9\s\.,!?~\-\"\'%/·…]")

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=_API_KEY)
    return _client


def _fix_logic_errors(result: CognitiveLoopResult) -> CognitiveLoopResult:
    """이탈했는데 클릭 True인 모순을 Python 레벨에서 보정한다."""
    if result.step2_selfish_filtering.is_dropped_out and result.step3_final_action.clicked:
        logger.warning(
            "Persona %s — 로직 모순 감지(이탈=True, 클릭=True) → 클릭 False로 보정",
            result.persona_id,
        )
        result.step3_final_action.clicked = False
        result.step3_final_action.action_reason = "그냥 넘겼다"
    return result


def _has_foreign_text(result: CognitiveLoopResult) -> bool:
    texts = [
        *result.step1_unconscious_reaction.keywords,
        result.step2_selfish_filtering.reason,
        result.step3_final_action.action_reason,
    ]
    return any(_KOREAN_ONLY.search(t) for t in texts)


# ── Single persona ─────────────────────────────────────────────────────────────

async def _simulate_one(
    persona: PersonaInput,
    ad_content: str,
    attempt: int = 0,
) -> CognitiveLoopResult | None:
    system = SYSTEM_PROMPT_TEMPLATE.format(
        age=persona.age,
        job=persona.job,
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
        optional_profile=build_optional_profile(persona),
    )
    user = USER_PROMPT_TEMPLATE.format(
        ad_content=ad_content,
        persona_id=persona.persona_id,
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
    )

    try:
        response = await _get_client().chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=_TEMPERATURE,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        text = response.choices[0].message.content
        result = _fix_logic_errors(CognitiveLoopResult(**json.loads(text)))

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
        logger.error("Persona %s — Groq auth error: check GROQ_API_KEY", persona.persona_id)
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
    # 미디어가 있으면 비전 모델로 광고 설명을 먼저 생성한다
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
    stage1 = []
    for p in screening:
        result = await _simulate_one(p, ad_content)
        stage1.append(result)

    stage2: list[CognitiveLoopResult | None] = []
    if remainder:
        logger.info("ad_id=%s | Stage-2 full batch: %d personas", ad_id, len(remainder))
        stage2 = await asyncio.gather(*[_simulate_one(p, ad_content) for p in remainder])

    all_results = [r for r in (*stage1, *stage2) if r is not None]

    if not all_results:
        raise RuntimeError("All persona simulations failed — check GROQ_API_KEY/quota")

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
