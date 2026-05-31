from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AdType(str, Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    CAROUSEL = "CAROUSEL"


# ── Step 1 ────────────────────────────────────────────────────────────────────

class UnconsciousReaction(BaseModel):
    """1.5초 안에 뇌에 박힌 첫인상"""

    keywords: List[str] = Field(
        description="Exactly 3 raw instinctive words — no analysis, no politeness"
    )
    appeal_score: int = Field(ge=1, le=5, description="Gut-feel score 1-5")

    @field_validator("keywords")
    @classmethod
    def exactly_three(cls, v: List[str]) -> List[str]:
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
    results: List[CognitiveLoopResult]
    metrics: AdMetrics


# ── Input ─────────────────────────────────────────────────────────────────────

class PersonaInput(BaseModel):
    persona_id: str
    age: int = Field(ge=13, le=80)
    job: str
    context: str = Field(
        description="Situational context right now, e.g. 'exhausted on packed subway after 10-hour shift'"
    )
    drop_off_trigger: str = Field(
        description="Specific things that make you instantly scroll away"
    )
    mbti: Optional[str] = None
    interests: Optional[List[str]] = None


class SimulationRequest(BaseModel):
    ad_id: str
    ad_content: str = Field(
        min_length=10,
        description="Full ad copy: headline, body, CTA, visual description"
    )
    ad_type: AdType = AdType.IMAGE
    personas: List[PersonaInput] = Field(min_length=1, max_length=50)
