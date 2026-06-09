from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_EMBED_MODEL = "text-embedding-3-small"
_EMBED_DIM = 1536
_MEMORY_FETCH_LIMIT = 10   # 벡터 검색 후 time-decay 재정렬 전 후보 수
_MEMORY_RETURN_LIMIT = 5   # 프롬프트에 주입할 최종 메모리 수
_DECAY_HALF_LIFE_DAYS = 30.0

_embed_client: AsyncOpenAI | None = None


def _get_embed_client() -> AsyncOpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _embed_client


async def _embed(text: str) -> list[float]:
    resp = await _get_embed_client().embeddings.create(
        model=_EMBED_MODEL,
        input=text[:8000],
    )
    return resp.data[0].embedding


def _vec_to_pg(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


def _time_decay(created_at: datetime, half_life_days: float = _DECAY_HALF_LIFE_DAYS) -> float:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    days_elapsed = (now - created_at).total_seconds() / 86400.0
    return math.exp(-math.log(2) * days_elapsed / half_life_days)


async def save_memory(
    pool,
    persona_id: str,
    tag: str,
    content: str,
    importance: int = 5,
) -> None:
    """광고 반응 이벤트를 persona_memories에 저장한다.

    tag: EVENT | PURCHASE | REFLECTION | CONVERSATION
    importance: 1-10 (Paper 1 — Generative Agents 중요도 점수)
    """
    if not pool:
        return
    try:
        embedding = await _embed(content)
        vec_str = _vec_to_pg(embedding)
        importance = max(1, min(10, importance))
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO persona_memories (persona_id, tag, content, embedding, importance)
                VALUES ($1, $2, $3, $4::vector, $5)
                """,
                persona_id, tag, content, vec_str, importance,
            )
        logger.debug("Memory saved: persona=%s tag=%s importance=%d", persona_id, tag, importance)
    except Exception as exc:
        logger.warning("Memory save failed (persona=%s): %s", persona_id, exc)


async def retrieve_memories(
    pool,
    persona_id: str,
    query_text: str,
) -> list[dict]:
    """관련 과거 기억을 3-factor 점수로 조회한다.

    Paper 1 (Generative Agents) 공식:
        score = (recency + importance_norm + relevance) / 3
    - recency      : time-decay (최신일수록 1에 가까움)
    - importance   : 1-10 저장값을 0-1로 정규화
    - relevance    : 코사인 유사도
    """
    if not pool:
        return []
    try:
        query_vec = await _embed(query_text)
        vec_str = _vec_to_pg(query_vec)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT tag, content, created_at, importance,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM persona_memories
                WHERE persona_id = $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                vec_str, persona_id, _MEMORY_FETCH_LIMIT,
            )

        results: list[dict] = []
        for r in rows:
            recency = _time_decay(r["created_at"])
            importance_norm = (r["importance"] - 1) / 9.0
            relevance = float(r["similarity"])
            score = (recency + importance_norm + relevance) / 3.0
            results.append({
                "tag": r["tag"],
                "content": r["content"],
                "score": score,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:_MEMORY_RETURN_LIMIT]

    except Exception as exc:
        logger.warning("Memory retrieval failed (persona=%s): %s", persona_id, exc)
        return []
