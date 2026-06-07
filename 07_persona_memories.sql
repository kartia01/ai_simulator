-- ============================================================
-- 페르소나 메모리 시스템 마이그레이션
-- 참고: Chu et al. (2025) — EVENT/REFLECTION/PURCHASE/CONVERSATION 태그
-- ============================================================

CREATE TABLE IF NOT EXISTS persona_memories (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id  TEXT        NOT NULL,
    tag         TEXT        NOT NULL CHECK (tag IN ('EVENT', 'PURCHASE', 'REFLECTION', 'CONVERSATION')),
    content     TEXT        NOT NULL,
    embedding   vector(1536),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 페르소나별 조회용 인덱스
CREATE INDEX IF NOT EXISTS idx_persona_memories_persona
    ON persona_memories (persona_id);

-- pgvector IVFFlat 인덱스 (코사인 유사도 검색)
-- lists=50: 메모리 테이블은 persona_templates보다 데이터가 적으므로 50으로 설정
CREATE INDEX IF NOT EXISTS idx_persona_memories_embedding
    ON persona_memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- tag별 조회 최적화 (REFLECTION 등 특정 태그 필터링 시)
CREATE INDEX IF NOT EXISTS idx_persona_memories_tag
    ON persona_memories (persona_id, tag);
