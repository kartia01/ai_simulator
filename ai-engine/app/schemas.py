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
    persona_id: str
    name: str
    age: int = Field(ge=13, le=80)
    job: str

    # 기존 필드
    platform: str | None = Field(default=None, description="광고를 보는 플랫폼 — e.g. '인스타그램', '유튜브'")
    context: str = Field(description="Situational context right now")
    drop_off_trigger: str = Field(description="Specific things that make you instantly scroll away")
    mbti: str | None = None
    interests: list[str] | None = None
    income_level: str | None = Field(default=None, description="소득 수준 — e.g. '저소득', '중산층', '고소득'")
    purchase_pattern: str | None = Field(default=None, description="구매 성향 — e.g. '충동구매 잦음', '비교 후 구매'")
    brand_sensitivity: str | None = Field(default=None, description="브랜드 민감도 — e.g. '브랜드 중시', '가격 중시'")
    typical_ad_behavior: str | None = Field(default=None, description="평소 광고 반응 패턴")
    value_keywords: str | None = Field(default=None, description="광고에서 반응하는 키워드")
    emotional_state: str | None = Field(default=None, description="현재 감정 상태")

    # IO Spec / Input.md 추가 필드
    segment: str | None = Field(default=None, description="세그먼트 — e.g. '30s_female_urban'")
    pain_points: list[str] | None = Field(default=None, description="해결하고 싶은 결핍 리스트")
    interest_keywords: list[str] | None = Field(default=None, description="관심사 키워드")
    price_threshold: int | None = Field(default=None, description="지출 가능한 최대 예산 (원)")
    brand_loyalty: float | None = Field(default=None, ge=0.0, le=1.0, description="브랜드 충성도 0.0~1.0")
    media_preferences: dict[str, float] | None = Field(default=None, description="매체별 선호도 점수")
    active_time_windows: list[str] | None = Field(default=None, description="주 미디어 소비 시간대")

    # 여태호 요구사항 — 부정적 앵커용
    ad_repellent_words: list[str] | None = Field(default=None, description="거부감을 주는 광고 표현")


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
