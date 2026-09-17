"""Structured feedback. Produced in M2 by the practice/feedback workflow; defined now so evidence
records, skill records and the export agree on the contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from dlp.domains.content.schemas import Skill


class FeedbackPoint(BaseModel):
    """One observation about the learner's language, tied to the evidence it comes from."""

    kind: Literal["strength", "error", "suggestion"]
    skill: Skill
    text_nl: str = Field(min_length=1)
    text_fa: str = ""
    quote: str = Field(default="", description="the learner's words the point is about, verbatim")
    correction: str = ""
    evidence_ids: list[str] = Field(min_length=1, description="evidence record ids that support this point")


class FeedbackReport(BaseModel):
    session_id: str
    step_key: str
    skill: Skill
    summary_nl: str
    summary_fa: str = ""
    points: list[FeedbackPoint]
    task_completed: bool
    evidence_ids: list[str] = Field(min_length=1)
    model_provider: str
    model_name: str
    prompt_version: str
