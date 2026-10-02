"""What the script writer must return, and the request bodies the video routes accept."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dlp.domains.stories.schemas import DraftQuestion, GlossaryItem, _clean

VideoKind = Literal["uitleg", "verhaal"]
KIND_LABELS: dict[str, str] = {"uitleg": "Uitleg", "verhaal": "Verhaal"}


class VideoScript(BaseModel):
    """A presenter script. The field names match the story draft so the same validator checks both.

    `paragraphs` are the scenes the presenter speaks one after the other; `keywords` is the word or
    short phrase shown on screen for each scene."""

    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=90)
    paragraphs: list[str] = Field(min_length=3, max_length=7,
                                  description="The spoken Dutch text, one scene per item, as the presenter says it")
    paragraphs_en: list[str] = Field(min_length=3, max_length=7, description="An English translation per scene")
    paragraphs_fa: list[str] = Field(min_length=3, max_length=7, description="A Persian translation per scene")
    keywords: list[str] = Field(min_length=3, max_length=7,
                                description="One Dutch word or short phrase per scene to show on screen")
    glossary: list[GlossaryItem] = Field(min_length=2, max_length=10)
    questions: list[DraftQuestion] = Field(min_length=2, max_length=3)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("title must not be blank")
        return value

    @field_validator("paragraphs", "paragraphs_en", "paragraphs_fa", "keywords")
    @classmethod
    def clean_items(cls, value: list[str]) -> list[str]:
        cleaned = [_clean(item) for item in value]
        if any(not item for item in cleaned):
            raise ValueError("items must not be blank")
        return cleaned


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
