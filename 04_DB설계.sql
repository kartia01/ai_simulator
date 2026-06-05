-- ============================================================
-- ClickMe DB 설계 문서
-- 작성일: 2026-06-04
-- DB: NeonDB (PostgreSQL + pgvector)
-- ============================================================

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUM 타입 정의
-- ============================================================

CREATE TYPE user_role AS ENUM ('admin', 'user');
CREATE TYPE project_status AS ENUM ('active', 'archived');
CREATE TYPE project_member_role AS ENUM ('owner', 'editor', 'viewer');
CREATE TYPE ad_input_type AS ENUM ('image', 'text', 'video', 'url');
CREATE TYPE ad_status AS ENUM ('pending', 'analyzing', 'completed', 'failed');
CREATE TYPE simulation_type AS ENUM ('ad_reaction', 'survey');
CREATE TYPE simulation_status AS ENUM ('pending', 'running', 'completed', 'failed');
CREATE TYPE chat_role AS ENUM ('user', 'assistant');
CREATE TYPE plan_type AS ENUM ('free', 'professional', 'enterprise');
CREATE TYPE campaign_objective AS ENUM ('awareness', 'conversion');

-- ============================================================
-- 조직 (결제 단위)
-- 여러 멤버가 하나의 플랜을 공유하는 단위
-- ============================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    plan_type       plan_type NOT NULL DEFAULT 'free',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 사용자
-- 관리자가 직접 생성. 소셜 로그인 없음. 자가 가입 없음.
-- ============================================================

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    name                VARCHAR(100) NOT NULL,
    role                user_role NOT NULL DEFAULT 'user',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Refresh Token (JWT 토큰 관리)
-- ============================================================

CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 프로젝트 (캠페인 단위)
-- 하나의 프로젝트 = 하나의 광고 캠페인
-- 여러 광고 시안 포함
-- ============================================================

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID NOT NULL REFERENCES users(id),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    status          project_status NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 프로젝트 멤버 (프로젝트 단위 협업)
-- 프로젝트 생성자는 자동으로 owner로 추가됨
-- ============================================================

CREATE TABLE project_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        project_member_role NOT NULL DEFAULT 'viewer',
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, user_id)
);

-- ============================================================
-- 광고 (업로드된 광고 시안)
-- 이미지/텍스트: 베이스라인
-- 영상/URL: 7/8 목표
-- ============================================================

CREATE TABLE ads (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by              UUID NOT NULL REFERENCES users(id),
    name                    VARCHAR(200) NOT NULL,
    input_type              ad_input_type NOT NULL,
    -- 이미지/영상: S3 저장 경로
    storage_path            TEXT,
    storage_url             TEXT,
    -- 텍스트 광고: 직접 입력 내용
    text_content            JSONB,
    -- URL 광고: 랜딩페이지 주소
    source_url              TEXT,
    -- 분석 결과
    analysis_status         ad_status NOT NULL DEFAULT 'pending',
    analysis_result         JSONB,
    analysis_confidence     FLOAT CHECK (analysis_confidence >= 0.0 AND analysis_confidence <= 1.0),
    analysis_error          TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 페르소나 템플릿
-- 재사용 가능한 페르소나 속성 저장
-- embedding: RAG 기반 페르소나 주입에 사용 (300명 이상)
-- ============================================================

CREATE TABLE persona_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100),
    cluster_id      VARCHAR(50),
    attributes      JSONB NOT NULL,
    embedding       vector(1536),
    is_public       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 시뮬레이션
-- 하나의 광고에 대해 N명의 페르소나 반응을 실행한 단위
-- ============================================================

CREATE TABLE simulations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_id               UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    created_by          UUID NOT NULL REFERENCES users(id),
    simulation_type     simulation_type NOT NULL DEFAULT 'ad_reaction',
    objective           campaign_objective NOT NULL DEFAULT 'conversion',
    status              simulation_status NOT NULL DEFAULT 'pending',
    -- 페르소나 설정
    persona_count       INTEGER NOT NULL DEFAULT 20,
    persona_config      JSONB,
    -- 집계 결과
    requested_count     INTEGER,
    received_count      INTEGER,
    sample_size         INTEGER,
    results_summary     JSONB,
    -- 비용 추적
    llm_cost_usd        FLOAT DEFAULT 0.0,
    -- 실행 시간
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 페르소나 응답
-- 시뮬레이션 내 페르소나 1명의 반응 데이터
-- 신호(signal)만 저장, KPI는 분석기가 산출
-- ============================================================

CREATE TABLE persona_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id       UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    -- 식별
    persona_id          VARCHAR(50) NOT NULL,
    producer_id         VARCHAR(100),
    segment             VARCHAR(100),
    -- 페르소나 속성 스냅샷
    persona_attributes  JSONB,
    -- 신호 데이터 (분석기 입력 계약 v1.2 기준)
    signals             JSONB NOT NULL,
    -- signals 필드 구조:
    -- {
    --   "attention": float 0.0~1.0,
    --   "sentiment": float -1.0~1.0,
    --   "click_intent": bool,
    --   "conversion_intent": bool,
    --   "comprehension": float 0.0~1.0,
    --   "recall": float 0.0~1.0
    -- }
    reasoning           TEXT,
    confidence          FLOAT CHECK (confidence >= 0.0 AND confidence <= 1.0),
    -- 이상치 처리
    is_outlier          BOOLEAN NOT NULL DEFAULT FALSE,
    outlier_reason      TEXT,
    -- LLM 메타데이터
    llm_model           VARCHAR(50),
    tokens_used         INTEGER,
    response_time_ms    INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Debate Agent 결과
-- 편향 제거를 위한 찬반 논쟁 결과 저장
-- [7/8 목표]
-- ============================================================

CREATE TABLE debate_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id       UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    positive_persona_id VARCHAR(50),
    negative_persona_id VARCHAR(50),
    positive_arguments  JSONB,
    counter_arguments   JSONB,
    synthesis           JSONB,
    adjusted_scores     JSONB,
    -- adjusted_scores 예시:
    -- { "click_intent_adjustment": -8.3, "bias_version": "v1.0" }
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 리포트
-- 시뮬레이션 분석 결과 최종 리포트
-- ============================================================

CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id   UUID NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE,
    report_data     JSONB NOT NULL,
    -- report_data 구조:
    -- {
    --   "executiveSummary": { "overallScore": int, "verdict": str, "topPriority": str },
    --   "detailedAnalysis": { kpi, funnel, bySegment, topDrivers, topObjections },
    --   "actionItems": { immediate, copySuggestions, ctaSuggestions, nextABTest }
    -- }
    pdf_url         TEXT,
    disclaimer      TEXT NOT NULL DEFAULT '본 결과는 AI 시뮬레이션 기반 예측입니다. 실제 광고 성과와 ±20~30% 오차가 있을 수 있습니다.',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Calibration 데이터
-- 예측 점수 vs 실제 광고 성과 비교 데이터
-- 미정: 포함 시점 결정 후 구현
-- ============================================================

CREATE TABLE calibration_data (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id           UUID REFERENCES simulations(id) ON DELETE SET NULL,
    predicted_ctr_score     FLOAT,
    actual_ctr_percent      FLOAT,
    industry                VARCHAR(50),
    platform                VARCHAR(50),
    ad_format               VARCHAR(30),
    submitted_by            UUID REFERENCES users(id),
    verified                BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 채팅 세션
-- 사용자의 대화 단위
-- ============================================================

CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id  UUID REFERENCES projects(id) ON DELETE SET NULL,
    title       VARCHAR(200) NOT NULL DEFAULT '새 채팅',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 채팅 메시지
-- ============================================================

CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        chat_role NOT NULL,
    content     TEXT NOT NULL,
    -- 연관 데이터 (시뮬레이션 결과, 리포트 등)
    metadata    JSONB,
    -- metadata 예시:
    -- { "simulationId": "uuid", "reportId": "uuid", "adId": "uuid" }
    tokens_used INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 생성 광고 (AI 이미지 생성)
-- 보관함 저장 기능 구현 (과금 로직 추후)
-- [7/8 목표]
-- ============================================================

CREATE TABLE generated_ads (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by          UUID NOT NULL REFERENCES users(id),
    prompt              TEXT NOT NULL,
    style               VARCHAR(50),
    aspect_ratio        VARCHAR(10) DEFAULT '1:1',
    -- 생성 결과
    status              ad_status NOT NULL DEFAULT 'pending',
    image_url           TEXT,
    storage_path        TEXT,
    -- 보관함 저장 여부 (과금 로직 추후)
    is_saved            BOOLEAN NOT NULL DEFAULT FALSE,
    saved_at            TIMESTAMPTZ,
    -- 생성 모델 (미정)
    generation_model    VARCHAR(50),
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 사용자 설정
-- ============================================================

CREATE TABLE user_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme           VARCHAR(10) NOT NULL DEFAULT 'light',  -- light / dark
    notifications   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 감사 로그 (관리자 추적)
-- ============================================================

CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(50),
    resource_id UUID,
    metadata    JSONB,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 인덱스
-- ============================================================

-- users
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- refresh_tokens
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- projects
CREATE INDEX idx_projects_organization ON projects(organization_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_status ON projects(status);

-- project_members
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);

-- ads
CREATE INDEX idx_ads_project ON ads(project_id);
CREATE INDEX idx_ads_created_by ON ads(created_by);
CREATE INDEX idx_ads_input_type ON ads(input_type);
CREATE INDEX idx_ads_status ON ads(analysis_status);

-- persona_templates
CREATE INDEX idx_persona_templates_cluster ON persona_templates(cluster_id);
CREATE INDEX idx_persona_templates_public ON persona_templates(is_public);
-- pgvector IVFFlat 인덱스 (RAG 기반 페르소나 주입용)
CREATE INDEX idx_persona_templates_embedding
    ON persona_templates USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- simulations
CREATE INDEX idx_simulations_project ON simulations(project_id);
CREATE INDEX idx_simulations_ad ON simulations(ad_id);
CREATE INDEX idx_simulations_created_by ON simulations(created_by);
CREATE INDEX idx_simulations_status ON simulations(status);

-- persona_responses
CREATE INDEX idx_persona_responses_simulation ON persona_responses(simulation_id);
CREATE INDEX idx_persona_responses_segment ON persona_responses(segment);
CREATE INDEX idx_persona_responses_outlier ON persona_responses(simulation_id, is_outlier);

-- debate_results
CREATE INDEX idx_debate_results_simulation ON debate_results(simulation_id);

-- reports
CREATE INDEX idx_reports_simulation ON reports(simulation_id);

-- calibration_data
CREATE INDEX idx_calibration_industry ON calibration_data(industry, platform);
CREATE INDEX idx_calibration_verified ON calibration_data(verified);

-- chat_sessions
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_project ON chat_sessions(project_id);
CREATE INDEX idx_chat_sessions_updated ON chat_sessions(updated_at DESC);

-- chat_messages
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(session_id, created_at);

-- generated_ads
CREATE INDEX idx_generated_ads_project ON generated_ads(project_id);
CREATE INDEX idx_generated_ads_created_by ON generated_ads(created_by);
CREATE INDEX idx_generated_ads_saved ON generated_ads(project_id, is_saved);

-- audit_logs
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- ============================================================
-- updated_at 자동 갱신 트리거
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_ads_updated_at
    BEFORE UPDATE ON ads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- 초기 데이터 (개발/테스트용)
-- ============================================================

-- 기본 조직 생성
INSERT INTO organizations (id, name, plan_type)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'ClickMe 관리 조직',
    'enterprise'
);

-- 최초 관리자 계정 생성
-- 비밀번호: 배포 시 환경 변수에서 주입, 아래는 placeholder
INSERT INTO users (id, organization_id, email, password_hash, name, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'admin@clickme.io',
    '$2a$12$PLACEHOLDER_HASH',  -- 실제 배포 시 bcrypt 해시로 교체
    '관리자',
    'admin'
);

-- ============================================================
-- 테이블 관계 요약
--
-- organizations
--     └── users (N)
--         └── refresh_tokens (N)
--         └── user_settings (1)
--     └── projects (N)
--         └── project_members (N)  ← users
--         └── ads (N)
--             └── simulations (N)
--                 └── persona_responses (N)
--                 └── debate_results (1)
--                 └── reports (1)
--                 └── calibration_data (N)
--         └── chat_sessions (N)  ← users
--             └── chat_messages (N)
--         └── generated_ads (N)
--
-- persona_templates (독립, RAG용)
-- audit_logs (독립, 추적용)
-- ============================================================
