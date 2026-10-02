"""Structured outputs the story writer must return, and the request bodies the routes accept."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Choice = Literal["a", "b"]


def _clean(value: str) -> str:
    return " ".join(value.split())


class GlossaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str = Field(min_length=1, max_length=60,
                      description="One Dutch word or short phrase exactly as it appears in the story")
    meaning_en: str = Field(min_length=1, max_length=120)
    meaning_fa: str = Field(min_length=1, max_length=120)
    example: str = Field(min_length=1, max_length=200, description="A short Dutch sentence from the story that uses the term")

    @field_validator("term", "meaning_en", "meaning_fa", "example")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("glossary fields must not be blank")
        return value


class DraftQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=200, description="A Dutch comprehension question about the story")
    options: list[str] = Field(min_length=3, max_length=3, description="Three Dutch answers; exactly one is correct")
    answer_index: int = Field(ge=0, le=2)
    evidence: str = Field(min_length=1, max_length=300,
                          description="The sentence from the story that proves the answer, copied exactly")

    @field_validator("prompt", "evidence")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("question text must not be blank")
        return value

    @field_validator("options")
    @classmethod
    def distinct(cls, value: list[str]) -> list[str]:
        cleaned = [_clean(item) for item in value]
        if any(not item for item in cleaned):
            raise ValueError("answer options must not be blank")
        if len({item.casefold() for item in cleaned}) != len(cleaned):
            raise ValueError("answer options must be distinct")
        return cleaned


class DraftChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Choice
    label: str = Field(min_length=1, max_length=140, description="What the reader can decide for the next episode, in Dutch")

    @field_validator("label")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("choice label must not be blank")
        return value


class EpisodeDraft(BaseModel):
    """What the writer returns. The validator decides whether it becomes an episode."""

    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=90)
    paragraphs: list[str] = Field(min_length=2, max_length=8, description="The Dutch story, one paragraph per item")
    paragraphs_en: list[str] = Field(min_length=2, max_length=8,
                                     description="An English translation, one item per Dutch paragraph")
    glossary: list[GlossaryItem] = Field(min_length=3, max_length=14)
    questions: list[DraftQuestion] = Field(min_length=2, max_length=3)
    recap: str = Field(min_length=1, max_length=400,
                       description="Two or three Dutch sentences summarising what happened, for the next episode")
    choices: list[DraftChoice] = Field(min_length=2, max_length=2)
    mood: str = Field(default="", max_length=30)

    @field_validator("title", "recap")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("text must not be blank")
        return value

    @field_validator("paragraphs", "paragraphs_en")
    @classmethod
    def clean_paragraphs(cls, value: list[str]) -> list[str]:
        cleaned = [_clean(item) for item in value]
        if any(not item for item in cleaned):
            raise ValueError("paragraphs must not be blank")
        return cleaned


class Translation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    translation: str = Field(min_length=1, max_length=1200)

    @field_validator("translation")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("translation must not be blank")
        return value


# --- request bodies ---------------------------------------------------------------------------------------

class RequestEpisodeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    theme: str = Field(default="", max_length=120, description="Optional wish for the next episode, in any language")


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    answers: dict[str, int] = Field(description="question index (as a string) to chosen option index")

    @field_validator("answers")
    @classmethod
    def bounded(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 3 or any(not key.isdigit() or not 0 <= choice <= 2 for key, choice in value.items()):
            raise ValueError("invalid answers")
        return value


class ChooseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choice: Choice


class RateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: Literal[-1, 1]


class TranslateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    paragraph_index: int = Field(ge=0, le=7)


class LevelBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str = Field(min_length=2, max_length=20)


class SaveWordBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str = Field(min_length=1, max_length=120)
    meaning_en: str = Field(default="", max_length=300)
    meaning_fa: str = Field(default="", max_length=300)
    example: str = Field(default="", max_length=400)
    source_kind: Literal["story", "library", "manual", "video"] = "manual"
    source_id: str = Field(default="", max_length=80)


class ReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=80)
    grade: Literal["again", "hard", "good", "easy"]


class ReadAloudResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paragraph_index: int
    transcript: str
    target_words: int
    matched_words: int
    missed: list[str]
    extra: list[str]
    points: int
