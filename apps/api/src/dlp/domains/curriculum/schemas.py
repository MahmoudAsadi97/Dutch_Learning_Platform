from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STAGE_IDS = (
    "pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1",
    "pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2",
)
Skill = Literal["reading", "listening", "speaking", "writing"]
SKILLS = ("reading", "listening", "speaking", "writing")


class Localized(BaseModel):
    nl: str = Field(min_length=1)
    en: str = Field(min_length=1)
    fa: str = Field(min_length=1)


class Question(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    prompt: Localized
    options: list[Localized] = Field(min_length=2, max_length=6)
    answer_index: int = Field(ge=0)
    explanation: Localized

    @model_validator(mode="after")
    def check_answer(self) -> Question:
        if self.answer_index >= len(self.options):
            raise ValueError("question answer is outside its options")
        return self


class Task(BaseModel):
    prompt: Localized
    criteria: list[Localized] = Field(min_length=1, max_length=8)
    sample: Localized
    sample_is_excerpt: bool = False
    min_words: int = Field(default=1, ge=1, le=1000)
    max_words: int = Field(default=200, ge=1, le=2000)

    @model_validator(mode="after")
    def check_bounds(self) -> Task:
        if self.max_words < self.min_words:
            raise ValueError("task word bounds are reversed")
        return self


class Grammar(BaseModel):
    id: str
    title: Localized
    explanation: Localized
    examples: list[Localized]
    practice: list[Question]


class Vocabulary(BaseModel):
    id: str
    term: str
    meaning: Localized
    example: Localized


class Lesson(BaseModel):
    story: Localized
    reading_questions: list[Question] = Field(min_length=1)
    listening: Localized
    listening_questions: list[Question] = Field(min_length=1)
    speaking: Task
    writing: Task


class ReceptiveTest(BaseModel):
    text: Localized
    questions: list[Question] = Field(min_length=4)


class Test(BaseModel):
    reading: ReceptiveTest
    listening: ReceptiveTest
    speaking: Task
    writing: Task


class Stage(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    title: Localized
    cefr_reference: str
    description: Localized
    grammar: list[Grammar] = Field(min_length=1)
    vocabulary: list[Vocabulary] = Field(min_length=1)
    lesson: Lesson
    test: Test

    @model_validator(mode="after")
    def unique_question_ids(self) -> Stage:
        groups = [self.lesson.reading_questions, self.lesson.listening_questions,
                  self.test.reading.questions, self.test.listening.questions]
        groups.extend(topic.practice for topic in self.grammar)
        for questions in groups:
            if len({q.id for q in questions}) != len(questions):
                raise ValueError("duplicate question IDs within an activity")
        return self


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal[1]
    stages: list[Stage]

    @model_validator(mode="after")
    def check_stages(self) -> Curriculum:
        if tuple(stage.id for stage in self.stages) != STAGE_IDS:
            raise ValueError("curriculum must contain the twelve ordered stages, without A3")
        return self


class CriterionReply(BaseModel):
    criterion_index: int = Field(ge=0)
    met: bool
    quote: str = Field(max_length=1800)
    feedback: Localized


class ProductiveReply(BaseModel):
    language_is_dutch: bool
    criteria: list[CriterionReply] = Field(min_length=1, max_length=8)
    feedback: Localized
