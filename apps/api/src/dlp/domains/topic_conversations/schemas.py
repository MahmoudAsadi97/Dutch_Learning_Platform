from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from dlp.domains.curriculum.schemas import STAGE_IDS, Localized


def normalized(text: str) -> str:
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold()))


def contains(text: str, phrase: str) -> bool:
    phrase = normalized(phrase)
    return bool(phrase) and f" {phrase} " in f" {normalized(text)} "


class Choice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=40)
    label: Localized
    aliases: list[str] = Field(min_length=1, max_length=12)
    valid: StrictBool


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=40)
    goal: Localized
    cue: Localized
    hint: Localized
    accepted: Localized
    example: Localized
    required_groups: list[list[str]] = Field(min_length=1, max_length=4)
    choices: list[Choice] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def bounded(self):
        if any(not 1 <= len(group) <= 12 or any(not normalized(alias) or len(alias) > 100 for alias in group)
               for group in self.required_groups):
            raise ValueError("language anchors must be small nonempty groups")
        if any(not any(contains(self.example.nl, alias) for alias in group) for group in self.required_groups):
            raise ValueError("authored example must demonstrate every language anchor")
        if self.choices:
            if len({choice.id for choice in self.choices}) != len(self.choices):
                raise ValueError("choices need distinct IDs")
            if not any(choice.valid for choice in self.choices) or not any(not choice.valid for choice in self.choices):
                raise ValueError("a fact decision needs valid and invalid alternatives")
            aliases = [normalized(alias) for choice in self.choices for alias in choice.aliases]
            if any(not alias or len(alias) > 100 for alias in aliases) or len(aliases) != len(set(aliases)):
                raise ValueError("choice aliases must be distinct and nonblank")
            hits = [choice for choice in self.choices if any(contains(self.example.nl, alias) for alias in choice.aliases)]
            if len(hits) != 1 or not hits[0].valid:
                raise ValueError("authored example must select exactly one valid factual choice")
        return self


class Blueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=80)
    stage_id: str
    topic_id: str = Field(max_length=60)
    title: Localized
    role: Localized
    setup: Localized
    opening: Localized
    success: Localized
    steps: list[Step] = Field(min_length=2, max_length=3)

    @model_validator(mode="after")
    def consistent(self):
        if self.stage_id not in STAGE_IDS or not self.topic_id.startswith(self.stage_id + "-t"):
            raise ValueError("conversation must refer to its own learning stage")
        if len({step.id for step in self.steps}) != len(self.steps):
            raise ValueError("conversation goals must be distinct")
        if len(self.setup.nl) > 1600 or any(len(copy.nl) > 500 for copy in (self.opening, self.success)):
            raise ValueError("scenario copy exceeds its bounded context or audio limit")
        for index, step in enumerate(self.steps):
            if any(len(copy.nl) > 500 for copy in (step.goal, step.cue, step.hint, step.example)):
                raise ValueError("turn copy exceeds its bounded audio limit")
            if index + 1 < len(self.steps) and len(step.accepted.nl + " " + self.steps[index + 1].cue.nl) > 500:
                raise ValueError("combined turn response exceeds its audio limit")
        def localized(value):
            if isinstance(value, dict):
                if "nl" in value and not all(str(value.get(lang, "")).strip() for lang in ("nl", "en", "fa")):
                    raise ValueError("conversation copy requires all three languages")
                for child in value.values():
                    localized(child)
            elif isinstance(value, list):
                for child in value:
                    localized(child)
        localized(self.model_dump())
        return self


class ConversationBank(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    review_status: Literal["unreviewed"]
    conversations: list[Blueprint] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def unique(self):
        if len({item.id for item in self.conversations}) != len(self.conversations):
            raise ValueError("conversation IDs must be unique")
        if len({(item.stage_id, item.topic_id) for item in self.conversations}) != len(self.conversations):
            raise ValueError("pilot conversations must cover ten different topics")
        return self


class TopicInterpretation(BaseModel):
    """A model proposes meaning only; it cannot choose a reply or alter scenario facts."""
    model_config = ConfigDict(extra="forbid")
    intent: Literal["respond", "repeat", "hint", "other"]
    goal_id: str = Field(max_length=40)
    met: StrictBool
    language_is_dutch: StrictBool
    quote: str = Field(max_length=800)
    choice_id: str = Field(default="", max_length=40)
