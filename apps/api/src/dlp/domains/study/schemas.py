from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from dlp.domains.curriculum.schemas import STAGE_IDS, Skill


class Copy(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nl: str = Field(min_length=1, max_length=12000)
    en: str = Field(min_length=1, max_length=12000)


class Word(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str = Field(min_length=1, max_length=180)
    part_of_speech: str = Field(default="expression", max_length=40)
    meaning: dict[str, str]
    example: Copy
    minimum_stage: str = "pre-a1"
    review_status: Literal["unreviewed"] = "unreviewed"

    @model_validator(mode="after")
    def complete_word(self):
        if self.minimum_stage not in STAGE_IDS:
            raise ValueError("guided vocabulary requires a known exposure stage")
        if not self.meaning.get("en", "").strip() or not set(self.meaning).issubset({"nl", "en"}):
            raise ValueError("guided vocabulary requires an English gloss and only Dutch/English support")
        return self


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9-]{1,60}$")
    nl: str = Field(min_length=1, max_length=160)
    en: str = Field(min_length=1, max_length=160)
    group: str = Field(min_length=1, max_length=100)
    keywords: list[str] = Field(default_factory=list, max_length=100)
    foundation_suitable: bool = False
    vocabulary: list[Word] = Field(default_factory=list, max_length=30)
    review_status: Literal["unreviewed"] = "unreviewed"
    order: int = Field(default=1, ge=1, le=200)
    short_questions: list[Copy] = Field(default_factory=list, max_length=6)
    short_question_samples: list[Copy] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def samples_match_questions(self):
        if self.short_question_samples and len(self.short_question_samples) != len(self.short_questions):
            raise ValueError("topic short answers must correspond to their authored questions")
        return self


class TopicDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    language_variety: str = "nl-BE"
    review_status: Literal["unreviewed"] = "unreviewed"
    topics: list[Topic] = Field(min_length=50, max_length=200)

    @model_validator(mode="after")
    def unique_topics(self):
        if len({topic.id for topic in self.topics}) != len(self.topics):
            raise ValueError("guided topics require unique IDs")
        return self


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["story", "practice", "pack", "reading"]
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class IndexDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    stages: dict[str, dict[Skill, dict[str, list[Source]]]]

    @model_validator(mode="after")
    def reading_sources_are_reading_only(self):
        for stage, skills in self.stages.items():
            if stage not in STAGE_IDS:
                raise ValueError("guided index requires a known learning stage")
            for skill, topics in skills.items():
                if skill != "reading" and any(source.source in {"story", "reading"}
                                               for sources in topics.values() for source in sources):
                    raise ValueError("authored reading sources belong only to the reading skill")
        return self


class CheckQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=110)
    kind: Literal["choice", "gap", "short"]
    prompt: Copy
    options: list[Copy] = Field(default_factory=list, max_length=6)
    answer_index: int | None = Field(default=None, ge=0)
    accepted_answers: list[str] = Field(default_factory=list, max_length=12)
    explanation: Copy

    @model_validator(mode="after")
    def answer_defined(self):
        if self.kind == "choice":
            if self.answer_index is None or self.answer_index >= len(self.options):
                raise ValueError("choice question requires a valid answer")
        elif not self.accepted_answers:
            raise ValueError("text question requires authored accepted answers")
        return self


class StoryQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=110)
    prompt: Copy
    options: list[Copy] = Field(min_length=2, max_length=6)
    answer_index: int = Field(ge=0)
    explanation: Copy

    @model_validator(mode="after")
    def valid_answer(self):
        if self.answer_index >= len(self.options):
            raise ValueError("guided story question answer is outside its options")
        return self


class GrammarPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Copy
    explanation: Copy
    examples: list[Copy] = Field(min_length=1, max_length=5)


class ReadingMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str
    topic_id: str = Field(pattern=r"^[a-z0-9-]{1,60}$")
    story_id: str = Field(min_length=1, max_length=100)
    grammar: list[GrammarPreparation] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def stage_bound_source(self):
        if self.stage_id not in STAGE_IDS or not self.story_id.startswith(self.stage_id + "-"):
            raise ValueError("reading mapping requires its original source stage")
        return self


class ReadingMapDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    mappings: list[ReadingMapping]

    @model_validator(mode="after")
    def distinct_sources(self):
        keys = [(mapping.stage_id, mapping.story_id) for mapping in self.mappings]
        if len(keys) != len(set(keys)):
            raise ValueError("an original reading may belong to only one topic")
        return self


class ProductiveTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: Copy
    sample: Copy
    min_words: int = Field(default=1, ge=1, le=1000)
    max_words: int = Field(default=350, ge=1, le=1500)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.min_words > self.max_words:
            raise ValueError("guided task word bounds are reversed")
        return self


class SpeakingOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    short_questions: list[ProductiveTask] = Field(default_factory=list, max_length=8)
    description: ProductiveTask | None = None
    discussion: ProductiveTask | None = None


class WritingOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    short: ProductiveTask | None = None
    extended: ProductiveTask | None = None


class ListeningSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Copy
    questions: list[CheckQuestion] = Field(min_length=1, max_length=12)


class ListeningOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sections: list[ListeningSection] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def ordered_task_types(self):
        for section, kind in zip(self.sections, ("gap", "choice", "short"), strict=True):
            if any(question.kind != kind for question in section.questions):
                raise ValueError("listening sections must use gap, choice and short tasks in that order")
        return self


class SourceListeningLesson(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: str
    activity_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    listening: ListeningOverride

    @model_validator(mode="after")
    def known_stage(self):
        if self.stage_id not in STAGE_IDS or not self.activity_id.startswith(f"{self.stage_id}-t-source-"):
            raise ValueError("source listening must retain a known stage and original activity identity")
        ids = [question.id for section in self.listening.sections for question in section.questions]
        if len(set(ids)) != len(ids):
            raise ValueError("source listening question IDs must be unique")
        return self


class SourceListeningDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    review_status: Literal["unreviewed"]
    lessons: list[SourceListeningLesson] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_activities(self):
        if len({lesson.activity_id for lesson in self.lessons}) != len(self.lessons):
            raise ValueError("source listening requires unique activity IDs")
        return self


class AuthoredLesson(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    topic_id: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    title: Copy
    review_status: Literal["unreviewed"] = "unreviewed"
    lines: list[Copy] = Field(min_length=8, max_length=12)
    questions: list[StoryQuestion] = Field(min_length=2, max_length=12)
    source_id: str | None = None
    words: list[Word] = Field(default_factory=list, max_length=20)
    grammar: list[GrammarPreparation] = Field(default_factory=list, max_length=4)
    speaking: SpeakingOverride | None = None
    writing: WritingOverride | None = None
    listening: ListeningOverride | None = None

    @model_validator(mode="after")
    def consistent_story(self):
        if any(len(line.nl) > 600 for line in self.lines):
            raise ValueError("guided story lines must fit sentence playback")
        if len({question.id for question in self.questions}) != len(self.questions):
            raise ValueError("guided story question IDs must be unique")
        if len({line.nl.casefold() for line in self.lines}) != len(self.lines):
            raise ValueError("guided story may not repeat a sentence to reach a line target")
        return self


class PackDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    language_variety: Literal["nl-BE"] = "nl-BE"
    stage_id: str
    review_status: Literal["unreviewed"]
    lessons: list[AuthoredLesson] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_lessons(self):
        if len({lesson.id for lesson in self.lessons}) != len(self.lessons):
            raise ValueError("guided packs require unique lesson IDs")
        return self


class ReadingLesson(AuthoredLesson):
    """An original reading scene, with its own plot and source-grounded preparation."""
    plot_key: str = Field(min_length=20, max_length=1000)
    words: list[Word] = Field(min_length=3, max_length=20)
    grammar: list[GrammarPreparation] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def original_reading(self):
        if self.source_id is not None:
            raise ValueError("original reading batches cannot relabel an existing source")
        if self.speaking is not None or self.writing is not None or self.listening is not None:
            raise ValueError("reading batches cannot publish unrequested skill variants")
        def normalized(value: str) -> str:
            return " ".join(value.casefold().split())
        lines = {(normalized(line.nl), normalized(line.en)) for line in self.lines}
        examples = [word.example for word in self.words]
        examples.extend(example for rule in self.grammar for example in rule.examples)
        if any(not word.meaning.get("nl", "").strip() for word in self.words):
            raise ValueError("reading vocabulary needs a Dutch definition and English gloss")
        if any((normalized(example.nl), normalized(example.en)) not in lines for example in examples):
            raise ValueError("reading vocabulary and grammar examples must preserve an exact bilingual story line")
        if len({normalized(word.term) for word in self.words}) != len(self.words):
            raise ValueError("reading vocabulary terms must be distinct")
        return self


class ReadingDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    language_variety: Literal["nl-BE"]
    stage_id: str
    review_status: Literal["unreviewed"]
    lessons: list[ReadingLesson] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def stage_bound_originals(self):
        if self.stage_id not in STAGE_IDS:
            raise ValueError("reading batch requires a known stage")
        if any(not lesson.id.startswith(f"{self.stage_id}-read-") for lesson in self.lessons):
            raise ValueError("reading lesson IDs must retain their stage and original reading identity")
        if len({lesson.id for lesson in self.lessons}) != len(self.lessons):
            raise ValueError("reading batches require unique lesson IDs")
        if any(word.minimum_stage != self.stage_id for lesson in self.lessons for word in lesson.words):
            raise ValueError("reading preparation must retain the authored exposure stage")
        return self


class FeedbackBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: Skill
    activity_id: str | None = Field(default=None, max_length=100, pattern=r"^[a-z0-9-]+$")
    part: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    question_id: str | None = Field(default=None, max_length=100, pattern=r"^[a-z0-9-]+$")
    kind: Literal["answers", "response"]
    text: str = Field(default="", max_length=8000)
    answers: dict[Annotated[str, Field(max_length=110)], StrictInt | Annotated[str, Field(max_length=1200)]] = Field(
        default_factory=dict, max_length=30)
    assistance_used: bool = False


class FeedbackCopy(Copy):
    nl: str = Field(min_length=1, max_length=250)
    en: str = Field(min_length=1, max_length=250)


class Correction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: str = Field(min_length=1, max_length=240)
    replacement: str = Field(max_length=320)
    category: Literal["spelling", "grammar", "word_order", "punctuation", "word_choice"]
    explanation: FeedbackCopy


class Dimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: int = Field(ge=0, le=10)
    grammar: int = Field(ge=0, le=10)
    vocabulary: int = Field(ge=0, le=10)
    organisation: int = Field(ge=0, le=10)


class CoachReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_is_dutch: bool
    dimensions: Dimensions
    summary: FeedbackCopy
    corrections: list[Correction] = Field(default_factory=list, max_length=5)
