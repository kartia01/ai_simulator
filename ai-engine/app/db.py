from __future__ import annotations

import logging
import os
import uuid as _uuid

import asyncpg

from .schemas import PersonaInput

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=5,
            statement_cache_size=0,
        )
        logger.info("DB pool initialized via DATABASE_URL")
        return

    host = os.getenv("DB_HOST")
    if not host:
        logger.warning("DATABASE_URL or DB_HOST not set — persona loading from DB unavailable")
        return

    ssl_mode = os.getenv("DB_SSL", "disable").lower()
    ssl: bool | None = True if ssl_mode in ("require", "true", "1") else False

    _pool = await asyncpg.create_pool(
        host=host,
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        min_size=1,
        max_size=5,
        ssl=ssl,
        statement_cache_size=0,
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


async def init_personas_table() -> None:
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name             TEXT NOT NULL,
                age              SMALLINT NOT NULL,
                job              TEXT NOT NULL,
                context          TEXT NOT NULL,
                drop_off_trigger TEXT NOT NULL,
                gender           TEXT,
                purchase_pattern TEXT,
                deal_prone_score DOUBLE PRECISION,
                price_threshold  INTEGER,
                brand_loyalty    DOUBLE PRECISION,
                platform         TEXT,
                emotional_state  TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS persona_interests (
                persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
                interest   TEXT NOT NULL
            )
        """)
    logger.info("personas table ready")


async def create_persona(persona: PersonaInput) -> str:
    if not _pool:
        raise RuntimeError("DB pool not initialized — set DATABASE_URL in .env")
    pid = _uuid.UUID(persona.persona_id)
    async with _pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO personas (id, name, age, job, context, drop_off_trigger,
                    gender, purchase_pattern, deal_prone_score, price_threshold,
                    brand_loyalty, platform, emotional_state)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            """, pid, persona.name, persona.age, persona.job,
                persona.context, persona.drop_off_trigger, persona.gender,
                persona.purchase_pattern, persona.deal_prone_score,
                persona.price_threshold, persona.brand_loyalty,
                persona.platform, persona.emotional_state)
            if persona.interests:
                await conn.executemany(
                    "INSERT INTO persona_interests (persona_id, interest) VALUES ($1, $2)",
                    [(pid, i) for i in persona.interests],
                )
    return str(pid)


async def update_persona(persona: PersonaInput) -> None:
    if not _pool:
        raise RuntimeError("DB pool not initialized — set DATABASE_URL in .env")
    pid = _uuid.UUID(persona.persona_id)
    async with _pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                UPDATE personas SET
                    name=$2, age=$3, job=$4, context=$5, drop_off_trigger=$6,
                    gender=$7, purchase_pattern=$8, deal_prone_score=$9,
                    price_threshold=$10, brand_loyalty=$11, platform=$12,
                    emotional_state=$13
                WHERE id = $1
            """, pid, persona.name, persona.age, persona.job,
                persona.context, persona.drop_off_trigger, persona.gender,
                persona.purchase_pattern, persona.deal_prone_score,
                persona.price_threshold, persona.brand_loyalty,
                persona.platform, persona.emotional_state)
            await conn.execute(
                "DELETE FROM persona_interests WHERE persona_id = $1", pid
            )
            if persona.interests:
                await conn.executemany(
                    "INSERT INTO persona_interests (persona_id, interest) VALUES ($1, $2)",
                    [(pid, i) for i in persona.interests],
                )


async def delete_persona(persona_id: str) -> None:
    if not _pool:
        raise RuntimeError("DB pool not initialized — set DATABASE_URL in .env")
    pid = _uuid.UUID(persona_id)
    async with _pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM persona_interests WHERE persona_id = $1", pid
            )
            await conn.execute("DELETE FROM personas WHERE id = $1", pid)


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
        emotional_state=row.get("emotional_state"),
    )
