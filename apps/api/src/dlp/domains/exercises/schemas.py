"""Request bodies and the typed views of exercise sessions.

A prompt is exactly what the browser may see before answering: no answer, no glosses of Dutch options, ids
that say nothing. What an answer reveals arrives in `Feedback`. The response models drop any key they do not
declare, which also keeps a stored key from leaking into a view.
"""
from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RequestId = Annotated[str, Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]
Source = Literal["stage_skill", "while_you_wait"]
# "almost" is shown in a neutral colour and is never a mistake; "accepted" is the learner's own overrule
Outcome = Literal["correct", "almost", "incorrect", "skipped", "done", "accepted", "heard", "not_heard"]
OptionId = Annotated[str, Field(min_length=1, max_length=16)]
# the kinds a session can hold besides its intro card; a client names those it can show
GradedKind = Literal["choice", "cloze_choice", "odd_one_out", "cloze_typed", "typed_recall", "flashcard",
                     "match_pairs", "de_het", "sentence_builder", "sentence_order", "listen_choose", "dictation",
                     "shadow"]
ReportReason = Literal["answer_wrong", "unclear", "sound", "other"]


class CreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    source: Source = "stage_skill"
    stage_id: str | None = Field(default=None, max_length=20)  # the learner's level when absent
    focus: Literal["words"] = "words"
    library_topic: str | None = Field(default=None, min_length=1, max_length=120)  # a library topic (topic.nl)
    size: int | None = Field(default=None, ge=5, le=12)
    fresh: bool = False  # start a new session even when one is open
    # only these kinds (a client that cannot show the others yet); recognition by choice is always among them
    kinds: list[GradedKind] | None = Field(default=None, min_length=1, max_length=13)

    @field_validator("kinds")
    @classmethod
    def _kinds(cls, kinds: list[str] | None) -> list[str] | None:
        if kinds is None:
            return None
        if "choice" not in kinds:
            raise ValueError("kinds must include choice")
        return sorted(set(kinds))


class AnswerValue(BaseModel):
    """One of these, by kind: an option; done (intro card); typed text; known (flashcard); pairs (left id to
    right id); bins (option id to de or het); order (tile or sentence ids, first to last)."""
    model_config = ConfigDict(extra="forbid")
    option: OptionId | None = None
    done: bool | None = None
    text: str | None = Field(default=None, max_length=300)
    known: bool | None = None
    pairs: dict[OptionId, OptionId] | None = Field(default=None, max_length=8)
    bins: dict[OptionId, Literal["de", "het"]] | None = Field(default=None, max_length=8)
    order: list[OptionId] | None = Field(default=None, max_length=12)


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    answer: AnswerValue
    hint_used: bool = False


class SkipBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    reason: Literal["unknown", "no_microphone", "no_audio"] = "unknown"


class OverrideBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId


class ReportBody(BaseModel):
    """"Meld een probleem": something about this exercise looks wrong to the learner."""
    model_config = ConfigDict(extra="forbid")
    request_id: RequestId
    reason: ReportReason
    note: str | None = Field(default=None, max_length=500)


class ReportResult(BaseModel):
    item_id: uuid.UUID
    reason: ReportReason


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
    cue: Text | None = None  # the sentence's translation, which tells siblings that fit the blank apart
    options: list[Option]


class Hint(BaseModel):
    first: str  # the first letter
    length: int


class ClozeTypedPrompt(BaseModel):
    kind: Literal["cloze_typed"]
    sentence: str
    cue: Text | None = None
    hint: Hint  # shown only when the learner asks; using it is reported with the answer


class TypedRecallPrompt(BaseModel):
    kind: Literal["typed_recall"]
    cue: Text  # the meaning in the support language
    hint: Hint


class FlashcardPrompt(BaseModel):
    kind: Literal["flashcard"]
    term: str


class MatchPairsPrompt(BaseModel):
    kind: Literal["match_pairs"]
    left: list[Option]  # Dutch words
    right: list[Option]  # meanings, in another order


class DeHetPrompt(BaseModel):
    kind: Literal["de_het"]
    bins: list[Literal["de", "het"]]
    options: list[Option]  # nouns without their article


class SentenceBuilderPrompt(BaseModel):
    kind: Literal["sentence_builder"]
    tiles: list[Option]  # words or word groups, in another order
    end: str  # the final punctuation
    cue: Text | None = None


class SentenceOrderPrompt(BaseModel):
    kind: Literal["sentence_order"]
    sentences: list[Option]


class ListenChoosePrompt(BaseModel):
    kind: Literal["listen_choose"]
    options: list[Option]  # written words; the spoken one comes from .../audio


class DictationPrompt(BaseModel):
    kind: Literal["dictation"]
    word_count: int  # how many words to type; the sentence comes from .../audio


class ShadowPrompt(BaseModel):
    kind: Literal["shadow"]
    sentence: str  # heard from .../audio, then said after the voice and sent to .../recording


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


Prompt = Annotated[ChoicePrompt | ClozePrompt | OddPrompt | IntroPrompt | ClozeTypedPrompt | TypedRecallPrompt
                   | FlashcardPrompt | MatchPairsPrompt | DeHetPrompt | SentenceBuilderPrompt | SentenceOrderPrompt
                   | ListenChoosePrompt | DictationPrompt | ShadowPrompt,
                   Field(discriminator="kind")]


class WordCard(BaseModel):
    library_id: str
    term: str
    meaning: Text
    example: Text


class DiffOp(BaseModel):
    op: Literal["same", "missing", "extra", "changed"]
    expected: str = ""
    given: str = ""


class PartResult(BaseModel):
    given: str
    correct: str
    ok: bool


class Feedback(BaseModel):
    outcome: Outcome
    correct: str | None = None  # the correct option id
    given: str | None = None  # the option the learner chose
    support: list[SupportOption] = []  # every option with its Dutch word and glosses
    explanation: Text | None = None
    word: WordCard | None = None
    sentence: str | None = None  # a cloze sentence, filled in
    odd_topic: Text | None = None  # odd one out: where the odd word belongs
    typed: str | None = None  # typed kinds: what the learner typed, the answer it was compared with, and why
    expected: str | None = None
    notes: list[str] = []
    diff: list[DiffOp] = []
    pairs: dict[str, PartResult] | None = None  # match pairs: per left id
    bins: dict[str, PartResult] | None = None  # de/het: per noun id
    cards: dict[str, WordCard] | None = None  # the words of a board
    order: list[str] | None = None  # the right order of tiles or sentences
    given_order: list[str] | None = None
    first_difference: int | None = None
    texts: list[str] | None = None  # the pieces in the right order
    translation: dict[str, list[str]] | None = None
    known: bool | None = None
    transcript: str | None = None  # shadowing: what the speech service heard; recognised words, never a score
    target_words: int | None = None
    matched_words: int | None = None
    missed: list[str] | None = None
    overridable: bool = False  # the learner may say the answer is right too


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
    overridden: int = 0  # answers the learner overruled; they never count towards completion
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
