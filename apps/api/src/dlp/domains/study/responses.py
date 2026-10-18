"""Public study contracts expose teaching content without private answer keys."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from dlp.domains.curriculum.schemas import Skill
from dlp.domains.study.schemas import Copy, Correction, GrammarPreparation

Score = Annotated[float, Field(ge=0, le=10)]


class StudyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TopicGroup(StudyResponse):
    id: str
    title: Copy


class TopicChoice(TopicGroup):
    group: str
    activity_count: int = Field(ge=0)
    available: bool
    availability_note: Copy | None


class StudyCatalogue(StudyResponse):
    stage_id: str
    skill: Skill
    groups: list[TopicGroup]
    topics: list[TopicChoice]
    total_topics: int = Field(ge=0)
    available_topics: int = Field(ge=0)


class PreparedWord(StudyResponse):
    id: str
    term: str
    part_of_speech: str
    meaning: Copy
    example: Copy


class StudyPreparation(StudyResponse):
    words: list[PreparedWord]
    grammar: list[GrammarPreparation]


class PublicQuestion(StudyResponse):
    id: str
    kind: Literal["choice", "gap", "short"]
    prompt: Copy
    options: list[Copy]


class PracticeQuestion(StudyResponse):
    id: str
    prompt: Copy
    sample: Copy | None


class StudyPart(StudyResponse):
    id: str
    title: Copy
    instructions: Copy
    prompt: Copy
    sample: Copy | None
    text: list[Copy]
    questions: list[PublicQuestion]
    practice_questions: list[PracticeQuestion]
    min_words: int = Field(ge=1)
    max_words: int = Field(ge=1)


class StudyContext(StudyResponse):
    title: Copy
    text: list[Copy]


class StudyPolicy(StudyResponse):
    ephemeral: Literal[True]
    pronunciation_assessed: Literal[False]
    recognized_certificate: Literal[False]
    audio_locale: Literal["nl-BE"]
    recording_max_seconds: float = Field(gt=0, le=60)


class StudyLesson(StudyResponse):
    stage_id: str
    topic_id: str
    skill: Skill
    title: Copy
    topic_title: Copy
    review_status: Literal["unreviewed"]
    preparation: StudyPreparation
    activities: list[TopicGroup]
    activity_id: str
    parts: list[StudyPart]
    context: StudyContext
    policy: StudyPolicy


class StudyDimensions(StudyResponse):
    task: Score | None
    grammar: Score | None
    vocabulary: Score | None
    organisation: Score | None
    pronunciation: None


class AnswerCheck(StudyResponse):
    id: str
    correct: bool | None
    review_required: bool
    answer: Copy
    explanation: Copy


class StudyFeedback(StudyResponse):
    status: Literal["evaluated", "fixture_unreviewed", "needs_review"]
    score: Score | None
    dimensions: StudyDimensions
    summary: Copy
    corrections: list[Correction]
    corrected_text: str | None = None
    checks: list[AnswerCheck]
    score_kind: Literal["comprehension", "answer_key_match", "semantic_comprehension", "language_response"] | None = None
    limited_answer_key: bool = False
    pronunciation_note: Copy
    assistance_used: bool = False
    ephemeral: Literal[True]


class TranscriptSegment(StudyResponse):
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str


class StudyTranscript(StudyResponse):
    text: str
    language: str
    segments: list[TranscriptSegment]


class TransientAudio(StudyResponse):
    stored: Literal[False]
    asset_id: None


class StudyTranscription(StudyResponse):
    transcript: StudyTranscript
    audio: TransientAudio
    ephemeral: Literal[True]
