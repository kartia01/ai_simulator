from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AdType(str, Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


# ── Step 1 ────────────────────────────────────────────────────────────────────

class UnconsciousReaction(BaseModel):
    """1.5초 안에 뇌에 박힌 첫인상"""

    emotions: list[str] = Field(
        description="Exactly 3 raw instinctive Korean words — no analysis, no politeness"
    )
    appeal_score: int = Field(ge=1, le=5, description="Gut-feel score 1-5")

    @field_validator("emotions")
    @classmethod
    def exactly_three(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError(f"Need exactly 3 emotions, got {len(v)}")
        return v


# ── Step 2 ────────────────────────────────────────────────────────────────────

class SelfishFiltering(BaseModel):
    """자기중심적 필터링: 상황+트리거 기반 이탈 판단 + IO Spec P1 신호"""

    is_dropped_out: bool = Field(description="True = scrolled past immediately")
    reason: str = Field(min_length=10, description="Raw internal monologue — why you stayed or bailed")
    sentiment: float = Field(ge=-1.0, le=1.0, description="호감 -1.0 강한 거부감 / 0.0 중립 / 1.0 강한 호감")
    comprehension: float = Field(ge=0.0, le=1.0, description="이해도 0.0 전혀 이해 못함 / 0.5 부분 이해 / 1.0 완전 이해")
    recall: float = Field(ge=0.0, le=1.0, description="기억 가능성 0.0 기억 못함 / 1.0 브랜드+메시지 모두 기억")


# ── Step 3 ────────────────────────────────────────────────────────────────────

class FinalAction(BaseModel):
    """최종 행동: 클릭 + 전환 의향 + 느낀점"""

    clicked: bool = Field(description="True = actually tapped the ad")
    conversion_intent: bool = Field(description="True = intent to purchase / sign up")
    action_reason: str = Field(min_length=5, description="The single thought that moved your thumb")
    impression: str = Field(min_length=5, description="이 광고에 대한 솔직한 한 줄 느낌")
    confidence: float = Field(ge=0.0, le=1.0, description="반응 확신도 0.0~1.0")
    reasoning_chain: str | None = Field(default=None, description="욕구→예산→브랜드 판단 내부 독백 요약")


# ── Internal aggregate ────────────────────────────────────────────────────────

class CognitiveLoopResult(BaseModel):
    persona_id: str
    step1_unconscious_reaction: UnconsciousReaction
    step2_selfish_filtering: SelfishFiltering
    step3_final_action: FinalAction


# ── IO Spec v1.4 §3-A ─────────────────────────────────────────────────────────

class PersonaReactionSignal(BaseModel):
    """분석기로 전달되는 완성 신호 (IO Spec v1.4 §3-A)"""

    schema_version: str = "1.4"
    producer_id: str = "sim_cognitive_loop_v2"
    creative_id: str
    objective: str

    persona_id: str
    persona_name: str
    persona_age: int
    persona_job: str
    segment: str

    # P0 필수
    attention: float = Field(ge=0.0, le=1.0)
    sentiment: float = Field(ge=-1.0, le=1.0)
    click_intent: bool
    conversion_intent: bool

    # P1 권장
    comprehension: float | None = Field(default=None, ge=0.0, le=1.0)
    reasoning: str | None = None
    recall: float | None = Field(default=None, ge=0.0, le=1.0)

    # P2 선택
    emotions: list[str] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    impression: str | None = None
    reasoning_chain: str | None = None


# ── Metrics ───────────────────────────────────────────────────────────────────

class AdMetrics(BaseModel):
    vtr: float = Field(description="View-Through Rate % — % who stayed past Step 2")
    ctr: float = Field(description="Click-Through Rate % — % who clicked at Step 3")
    cvr: float = Field(description="Conversion Rate % — % with conversion_intent")
    dropout_rate: float = Field(description="% who bailed at Step 2")
    avg_appeal_score: float = Field(description="Average Step 1 gut-feel score (1-5)")
    avg_attention: float = Field(description="Average attention 0.0~1.0")
    avg_sentiment: float = Field(description="Average sentiment -1.0~1.0")
    outlier_count: int = Field(default=0, description="IQR 이상치로 제외된 응답 수")


class SimulationResponse(BaseModel):
    ad_id: str
    total_personas: int
    results: list[PersonaReactionSignal]
    metrics: AdMetrics


# ── Input ─────────────────────────────────────────────────────────────────────

class PersonaInput(BaseModel):
    # ── 필수 ──────────────────────────────────────────────────────────────────
    persona_id: str
    name: str
    age: int = Field(ge=13, le=80)
    job: str
    context: str = Field(description="지금 이 순간의 상황")
    drop_off_trigger: str = Field(description="즉시 스크롤을 넘기게 만드는 조건")

    # ── 인구통계 ──────────────────────────────────────────────────────────────
    gender: str | None = Field(default=None, description="성별 — e.g. '남성', '여성'")

    # ── 관심사 ────────────────────────────────────────────────────────────────
    interests: list[str] | None = None

    # ── 구매 성향 ─────────────────────────────────────────────────────────────
    purchase_pattern: str | None = Field(default=None, description="구매 성향 — e.g. '충동구매 잦음', '비교 후 구매'")
    deal_prone_score: float | None = Field(default=None, ge=0.0, le=1.0, description="가격 할인 민감도 0.0~1.0")
    price_threshold: int | None = Field(default=None, description="지출 가능한 최대 예산 (원)")

    # ── 제품 관여도 ───────────────────────────────────────────────────────────
    brand_loyalty: float | None = Field(default=None, ge=0.0, le=1.0, description="브랜드 충성도 0.0~1.0")

    # ── 상황 / 심리 ───────────────────────────────────────────────────────────
    platform: str | None = Field(default=None, description="광고를 보는 플랫폼 — e.g. '인스타그램', '유튜브'")
    mbti: str | None = None
    emotional_state: str | None = Field(default=None, description="현재 감정 상태")


class SimulationRequest(BaseModel):
    ad_id: str
    ad_content: str = Field(
        default="",
        description="Full ad copy: headline, body, CTA, visual description",
    )
    ad_type: AdType = AdType.IMAGE
    objective: str = Field(
        default="conversion",
        description="캠페인 목적 — 'awareness' | 'conversion'",
    )
    product_price: int | None = Field(
        default=None,
        description="시뮬레이션 대상 상품 가격 (원) — conversion 캠페인에서 price_threshold와 비교",
    )
    personas: list[PersonaInput] = Field(min_length=1, max_length=50)
    image_base64: str | None = Field(default=None, description="Base64-encoded image (JPEG/PNG/GIF/WEBP)")
    video_base64: str | None = Field(default=None, description="Base64-encoded video (MP4/MOV/AVI)")
    media_content_type: str | None = Field(default=None, description="MIME type — e.g. 'image/jpeg'")
