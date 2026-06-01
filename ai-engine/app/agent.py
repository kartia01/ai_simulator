from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import List

import httpx

from .prompts import SYSTEM_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE
from .schemas import (
    AdMetrics,
    AdType,
    CognitiveLoopResult,
    PersonaInput,
    SimulationResponse,
)

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("GEMINI_API_KEY")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.0-flash:generateContent"
)

MAX_RETRIES = 3
SCREENING_COUNT = 3


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
    )
    user = USER_PROMPT_TEMPLATE.format(
        ad_content=ad_content,
        persona_id=persona.persona_id,
        context=persona.context,
        drop_off_trigger=persona.drop_off_trigger,
    )

    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.88,
            "maxOutputTokens": 600,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                _GEMINI_URL,
                params={"key": _API_KEY},
                json=body,
            )

        if r.status_code == 429:
            if attempt >= MAX_RETRIES:
                logger.error("Persona %s — gave up after rate limit retries", persona.persona_id)
                return None
            wait = 2 ** attempt * 5
            logger.warning(
                "Persona %s — 429 rate limit, waiting %ds (attempt %d)",
                persona.persona_id, wait, attempt + 1,
            )
            await asyncio.sleep(wait)
            return await _simulate_one(persona, ad_content, attempt + 1)

        if r.status_code in (401, 403):
            logger.error(
                "Persona %s — Gemini auth error %d: %s",
                persona.persona_id, r.status_code, r.text[:300],
            )
            return None

        r.raise_for_status()

        data = r.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(
                f"No candidates in Gemini response "
                f"(promptFeedback={data.get('promptFeedback')})"
            )
        candidate = candidates[0]
        if "content" not in candidate:
            raise ValueError(
                f"Candidate has no content "
                f"(finishReason={candidate.get('finishReason')})"
            )
        text = candidate["content"]["parts"][0]["text"]
        return CognitiveLoopResult(**json.loads(text))

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
    personas: List[PersonaInput],
    ad_content: str,
    ad_id: str,
    ad_type: AdType = AdType.IMAGE,
) -> SimulationResponse:
    screening = personas[:SCREENING_COUNT]
    remainder = personas[SCREENING_COUNT:]

    logger.info("ad_id=%s | Stage-1 screening: %d personas", ad_id, len(screening))
    stage1 = []
    for p in screening:
        result = await _simulate_one(p, ad_content)
        stage1.append(result)
        await asyncio.sleep(1)  # 무료 티어 rate limit 방지

    stage2: list = []
    if remainder:
        await asyncio.sleep(3)
        logger.info("ad_id=%s | Stage-2 full batch: %d personas", ad_id, len(remainder))
        for p in remainder:
            result = await _simulate_one(p, ad_content)
            stage2.append(result)
            await asyncio.sleep(1)

    all_results = [r for r in (*stage1, *stage2) if r is not None]

    if not all_results:
        raise RuntimeError("All persona simulations failed — check Gemini API key/quota")

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

def _calc_metrics(results: List[CognitiveLoopResult]) -> AdMetrics:
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
