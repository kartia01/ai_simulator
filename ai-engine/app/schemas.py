from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AdType(str, Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


# ── Step 1 ────────────────────────────────────────────────────────────────────

class UnconsciousReaction(BaseModel):
    """1.5초 안에 뇌에 박힌 첫인상"""

    keywords: list[str] = Field(
        description="Exactly 3 raw instinctive words — no analysis, no politeness"
    )
    appeal_score: int = Field(ge=1, le=5, description="Gut-feel score 1-5")

    @field_validator("keywords")
    @classmethod
    def exactly_three(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError(f"Need exactly 3 keywords, got {len(v)}")
        return v


# ── Step 2 ────────────────────────────────────────────────────────────────────

class SelfishFiltering(BaseModel):
    """자기중심적 필터링: 상황+트리거 기반 이탈 판단"""

    is_dropped_out: bool = Field(
        description="True = scrolled past immediately"
    )
    reason: str = Field(
        min_length=10,
        description="Raw internal monologue — why you stayed or bailed"
    )


# ── Step 3 ────────────────────────────────────────────────────────────────────

class FinalAction(BaseModel):
    """최종 행동: 클릭 or 무시"""

    clicked: bool = Field(description="True = actually tapped the ad")
    action_reason: str = Field(
        min_length=5,
        description="The single thought that moved your thumb"
    )


# ── Aggregate ─────────────────────────────────────────────────────────────────

class CognitiveLoopResult(BaseModel):
    persona_id: str
    step1_unconscious_reaction: UnconsciousReaction
    step2_selfish_filtering: SelfishFiltering
    step3_final_action: FinalAction


class AdMetrics(BaseModel):
    vtr: float = Field(description="View-Through Rate %  — % who stayed past Step 2")
    ctr: float = Field(description="Click-Through Rate % — % who clicked at Step 3")
    dropout_rate: float = Field(description="% who bailed at Step 2")
    avg_appeal_score: float = Field(description="Average Step 1 gut-feel score")


class SimulationResponse(BaseModel):
    ad_id: str
    total_personas: int
    results: list[CognitiveLoopResult]
    metrics: AdMetrics


# ── Input ─────────────────────────────────────────────────────────────────────

class PersonaInput(BaseModel):
    persona_id: str
    name: str
    age: int = Field(ge=13, le=80)
    job: str
    platform: str | None = Field(
        default=None,
        description="광고를 보는 플랫폼 — e.g. '인스타그램', '유튜브', '틱톡', '네이버'"
    )
    context: str = Field(
        description="Situational context right now, e.g. 'exhausted on packed subway after 10-hour shift'"
    )
    drop_off_trigger: str = Field(
        description="Specific things that make you instantly scroll away"
    )
    mbti: str | None = None
    interests: list[str] | None = None
    income_level: str | None = Field(
        default=None,
        description="소득 수준 — e.g. '저소득', '중산층', '고소득'"
    )
    purchase_pattern: str | None = Field(
        default=None,
        description="구매 성향 — e.g. '충동구매 잦음', '비교 후 구매', '거의 안 삼'"
    )
    brand_sensitivity: str | None = Field(
        default=None,
        description="브랜드 민감도 — e.g. '브랜드 중시', '가격 중시', '무관심'"
    )
    typical_ad_behavior: str | None = Field(
        default=None,
        description="평소 광고 반응 패턴 — e.g. '광고 거의 클릭 안 함, 할인 정보만 반응'"
    )
    value_keywords: str | None = Field(
        default=None,
        description="광고에서 반응하는 키워드 — e.g. '가성비, 무료배송, 한정특가'"
    )
    emotional_state: str | None = Field(
        default=None,
        description="현재 감정 상태 — e.g. '스트레스 높음', '평온', '피곤함', '기분 좋음', '무료함'"
    )


class SimulationRequest(BaseModel):
    ad_id: str
    ad_content: str = Field(
        default="",
        description="Full ad copy: headline, body, CTA, visual description (optional when media provided)"
    )
    ad_type: AdType = AdType.IMAGE
    personas: list[PersonaInput] = Field(min_length=1, max_length=50)
    image_base64: str | None = Field(
        default=None,
        description="Base64-encoded image file (JPEG/PNG/GIF/WEBP)"
    )
    video_base64: str | None = Field(
        default=None,
        description="Base64-encoded video file (MP4/MOV/AVI)"
    )
    media_content_type: str | None = Field(
        default=None,
        description="MIME type of uploaded media, e.g. 'image/jpeg', 'video/mp4'"
    )
