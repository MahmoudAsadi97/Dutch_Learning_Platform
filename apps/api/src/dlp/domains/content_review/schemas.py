from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1, max_length=160)
    category: Literal["grounding", "ambiguity", "language", "translation", "difficulty", "repetition"]
    quote: str = Field(min_length=1, max_length=160)
    explanation: str = Field(min_length=1, max_length=500)

    @field_validator("path", "quote", "explanation")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("review text must not be blank")
        return value.strip()


class ReviewReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=500)
    issues: list[ReviewIssue] = Field(max_length=12)

    @field_validator("summary")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("summary must not be blank")
        return value.strip()


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic_ids: list[str] = Field(min_length=1, max_length=5)
    retry_failed: bool = False

    @field_validator("topic_ids")
    @classmethod
    def unique_ids(cls, value):
        if len(set(value)) != len(value) or any(not item or len(item) > 60 for item in value):
            raise ValueError("select one to five different topics")
        return value
