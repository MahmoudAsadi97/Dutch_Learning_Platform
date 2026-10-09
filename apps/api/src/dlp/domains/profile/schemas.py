"""Request bodies and response shapes for /me. Validation rejects unknown stages, goals outside the three
sizes and extra fields; the response models keep the HTTP contract typed."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from dlp.domains.curriculum.schemas import STAGE_IDS

SupportMode = Literal["nl-en", "nl-fa", "nl-fa-en"]
GlossMode = Literal["auto", "on", "off"]
DailyGoal = Literal[10, 20, 30]
# Why the learner studies, chosen in the welcome; "" is no answer. A closed list keeps free text out of the profile.
StatedGoal = Literal["", "werk", "studie", "dagelijks leven", "inburgering", "voor mezelf"]


def _stage(value: str) -> str:
    if value not in STAGE_IDS:
        raise ValueError("unknown learning stage")
    return value


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str | None = None
    daily_goal_points: DailyGoal | None = None
    support_mode: SupportMode | None = None
    gloss_mode: GlossMode | None = None
    stated_goal: StatedGoal | None = None

    @field_validator("stage_id")
    @classmethod
    def known_stage(cls, value: str | None) -> str | None:
        return None if value is None else _stage(value)

    @model_validator(mode="after")
    def no_null_for_required(self) -> ProfileUpdate:
        # only support_mode may be cleared; an explicit null elsewhere is a client error, not a database one
        for name in ("stage_id", "daily_goal_points", "gloss_mode", "stated_goal"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class OnboardingBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    support_mode: SupportMode
    stage_id: str
    daily_goal_points: DailyGoal = 20
    stated_goal: StatedGoal = ""

    @field_validator("stage_id")
    @classmethod
    def known_stage(cls, value: str) -> str:
        return _stage(value)


class LearnerView(BaseModel):
    email: str
    display_name: str


class ProfileView(BaseModel):
    stage_id: str
    daily_goal_points: int
    support_mode: SupportMode | None
    gloss_mode: GlossMode
    stated_goal: str
    onboarded_at: str | None
    earned_stage_id: str | None
    suggested_stage_id: str | None


class MeView(BaseModel):
    learner: LearnerView
    profile: ProfileView
    features: dict[str, Any]


class OnboardingView(MeView):
    already_onboarded: bool
    episode: dict[str, Any] | None
