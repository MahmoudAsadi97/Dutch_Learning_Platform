from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str = Field(min_length=2, max_length=20)
    request_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


class RankedActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=90)
    evidence_ids: list[str] = Field(default_factory=list, max_length=2)


class PlanRanking(BaseModel):
    """The model may reorder vetted activities, never invent activities or learner diagnoses."""
    model_config = ConfigDict(extra="forbid")
    activities: list[RankedActivity] = Field(min_length=3, max_length=3)
