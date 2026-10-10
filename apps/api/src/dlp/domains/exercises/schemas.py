"""Request bodies and the typed views of exercise sessions.

A prompt is exactly what the browser may see before answering: no answer, no glosses of Dutch options, ids
that say nothing. What an answer reveals arrives in `Feedback`. The response models drop any key they do not
declare, which also keeps a stored key from leaking into a view.
"""
from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

RequestId = Annotated[str, Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]
Source = Literal["stage_skill", "while_you_wait"]
Outcome = Literal["correct", "incorrect", "skipped", "done"]


class CreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    source: Source = "stage_skill"
    stage_id: str | None = Field(default=None, max_length=20)  # the learner's level when absent
    focus: Literal["words"] = "words"
    library_topic: str | None = Field(default=None, min_length=1, max_length=120)  # a library topic (topic.nl)
    size: int | None = Field(default=None, ge=5, le=12)
    fresh: bool = False  # start a new session even when one is open


class AnswerValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    option: str | None = Field(default=None, min_length=1, max_length=16)
    done: bool | None = None


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    answer: AnswerValue
    hint_used: bool = False


class SkipBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    reason: Literal["unknown", "no_microphone", "no_audio"] = "unknown"


class FinishBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    early: bool = False


class Text(BaseModel):
    nl: str | None = None
    en: str | None = None
    fa: str | None = None


class Option(BaseModel):
    id: str
    nl: str | None = None
    en: str | None = None
    fa: str | None = None


class SupportOption(Option):
    definition: str | None = None


class ChoicePrompt(BaseModel):
    kind: Literal["choice"]
    direction: Literal["meaning", "term", "definition", "question"]
    stem: Text
    options: list[Option]


class ClozePrompt(BaseModel):
    kind: Literal["cloze_choice"]
    sentence: str  # "___" marks the blank
    cue: Text | None = None  # the sentence's translation, when siblings would also fit
    options: list[Option]


class OddPrompt(BaseModel):
    kind: Literal["odd_one_out"]
    topic: Text
    options: list[Option]


class IntroWord(BaseModel):
    term: str
    meaning: Text
    example: Text


class IntroPrompt(BaseModel):
    kind: Literal["intro"]
    words: list[IntroWord]


Prompt = Annotated[ChoicePrompt | ClozePrompt | OddPrompt | IntroPrompt, Field(discriminator="kind")]


class WordCard(BaseModel):
    library_id: str
    term: str
    meaning: Text
    example: Text


class Feedback(BaseModel):
    outcome: Outcome
    correct: str | None = None  # the correct option id
    given: str | None = None  # the option the learner chose
    support: list[SupportOption] = []  # every option with its Dutch word and glosses
    explanation: Text | None = None
    word: WordCard | None = None
    sentence: str | None = None  # a cloze sentence, filled in
    odd_topic: Text | None = None  # odd one out: where the odd word belongs


class Progress(BaseModel):
    closed: int  # graded items done
    total: int  # graded items
    queued: int  # missed once and asked again at the end


class ItemView(BaseModel):
    id: uuid.UUID
    position: int
    kind: str
    skill: str
    state: Literal["open", "closed"]
    attempts_left: int
    prompt: Prompt
    feedback: Feedback | None = None  # once the item is closed


class MissedItem(BaseModel):
    ref: str
    term: str | None = None
    expected: str | None = None


class Suggestion(BaseModel):
    key: str
    term: str
    meaning_en: str
    meaning_fa: str


class KindCount(BaseModel):
    total: int
    first_try_correct: int


class Summary(BaseModel):
    items_total: int
    answered: int
    first_try_correct: int
    fixed_on_retry: int
    skipped: int
    points_earned: int  # items and the session bonus
    session_bonus: int
    by_kind: dict[str, KindCount]
    missed: list[MissedItem]
    suggestions: list[Suggestion]


class SessionView(BaseModel):
    id: uuid.UUID
    source: str
    stage_id: str
    focus: str
    library_topic: str | None = None
    status: Literal["active", "finished", "abandoned"]
    content_status: Literal["unreviewed"] = "unreviewed"
    resumed: bool = False
    items: list[ItemView]
    next_item_id: uuid.UUID | None = None
    progress: Progress
    summary: Summary | None = None


class AnswerResult(BaseModel):
    item_id: uuid.UUID
    attempt: int
    outcome: Outcome
    closed: bool
    requeue: bool  # asked once more at the end
    attempts_left: int
    feedback: Feedback
    points: int
    progress: Progress
    next_item_id: uuid.UUID | None = None
    goal_reached: bool | None = None


class FinishResult(BaseModel):
    id: uuid.UUID
    status: Literal["finished"]
    summary: Summary
    points: int
    goal_reached: bool | None = None
