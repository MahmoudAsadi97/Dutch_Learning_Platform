"""Legacy request shapes retained so old clients receive a controlled retirement response."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

VideoKind = Literal["uitleg", "verhaal"]
KIND_LABELS: dict[str, str] = {"uitleg": "Uitleg", "verhaal": "Verhaal"}


# --- request bodies ---------------------------------------------------------------------------------------

class RequestVideoBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    stage_id: str = Field(min_length=2, max_length=20)
    topic: str = Field(default="", max_length=120, description="What the video should be about, in any language")
    kind: VideoKind = "uitleg"


class VideoAnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    answers: dict[str, int]

    @field_validator("answers")
    @classmethod
    def bounded(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 3 or any(not key.isdigit() or not 0 <= choice <= 2 for key, choice in value.items()):
            raise ValueError("invalid answers")
        return value


class VideoRateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: Literal[-1, 1]


class VideoWordBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str = Field(min_length=1, max_length=120)
