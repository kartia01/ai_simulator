from __future__ import annotations

import logging
import os

import asyncpg

from .schemas import PersonaInput

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    host = os.getenv("DB_HOST")
    if not host:
        logger.warning("DB_HOST not set — persona loading from DB unavailable")
        return
    _pool = await asyncpg.create_pool(
        host=host,
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        min_size=1,
        max_size=5,
        ssl="require",
        statement_cache_size=0,  # pgbouncer 트랜잭션 모드 호환
    )
    logger.info("DB pool initialized (host=%s port=%s)", host, os.getenv("DB_PORT"))


def get_pool() -> asyncpg.Pool | None:
    return _pool


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("DB pool closed")


async def init_memory_table() -> None:
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS persona_memories (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                persona_id  TEXT NOT NULL,
                tag         TEXT NOT NULL CHECK (tag IN ('EVENT', 'PURCHASE', 'REFLECTION', 'CONVERSATION')),
                content     TEXT NOT NULL,
                embedding   vector(1536),
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        # Paper 1 (Generative Agents): importance 컬럼 마이그레이션
        try:
            await conn.execute("""
                ALTER TABLE persona_memories
                ADD COLUMN IF NOT EXISTS importance SMALLINT NOT NULL DEFAULT 5
            """)
        except Exception as e:
            logger.warning("importance 컬럼 추가 스킵: %s", e)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_persona_memories_persona
            ON persona_memories (persona_id)
        """)
        # ivfflat 인덱스는 데이터가 있어야 생성 가능하므로 실패해도 무시
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_persona_memories_embedding
                ON persona_memories USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 50)
            """)
        except Exception as e:
            logger.warning("ivfflat 인덱스 생성 스킵 (데이터 없음 또는 미지원): %s", e)
    logger.info("persona_memories table ready")


async def get_all_personas() -> list[PersonaInput]:
    return await _fetch_personas("SELECT * FROM personas", [])


async def get_personas_by_ids(ids: list[str]) -> list[PersonaInput]:
    return await _fetch_personas(
        "SELECT * FROM personas WHERE id::text = ANY($1)", [ids]
    )


async def _fetch_personas(sql: str, args: list) -> list[PersonaInput]:
    if not _pool:
        raise RuntimeError("DB pool not initialized — set DB_HOST in .env")

    async with _pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)
        if not rows:
            return []

        persona_ids = [str(r["id"]) for r in rows]
        interest_rows = await conn.fetch(
            "SELECT persona_id, interest FROM persona_interests"
            " WHERE persona_id::text = ANY($1)",
            persona_ids,
        )

    interests_map: dict[str, list[str]] = {}
    for ir in interest_rows:
        interests_map.setdefault(str(ir["persona_id"]), []).append(ir["interest"])

    return [_row_to_persona(r, interests_map.get(str(r["id"]), [])) for r in rows]


def _row_to_persona(row: asyncpg.Record, interests: list[str]) -> PersonaInput:
    return PersonaInput(
        persona_id=str(row["id"]),
        name=row["name"],
        age=row["age"],
        job=row["job"],
        context=row["context"],
        drop_off_trigger=row["drop_off_trigger"],
        gender=row.get("gender"),
        interests=interests or None,
        purchase_pattern=row.get("purchase_pattern"),
        deal_prone_score=row.get("deal_prone_score"),
        price_threshold=row.get("price_threshold"),
        brand_loyalty=row.get("brand_loyalty"),
        platform=row.get("platform"),
        mbti=row.get("mbti"),
        emotional_state=row.get("emotional_state"),
    )
