"""Versioned, original practice banks. Browsing never creates assessment credit."""
from __future__ import annotations

import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question
from dlp.domains.curriculum.service import CurriculumError


class LibraryWord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    term: str = Field(min_length=1, max_length=180)
    topic: Localized
    meaning: Localized
    example: Localized


class StoryQuestion(BaseModel):
    prompt: Localized
    options: list[Localized] = Field(min_length=2, max_length=6)
    answer_index: int = Field(ge=0)
    explanation: Localized

    @model_validator(mode="after")
    def answer_exists(self):
        if self.answer_index >= len(self.options):
            raise ValueError("story answer is outside its options")
        return self


class LibraryStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # The derived practice-question ID adds "-understand" and must fit Question's 80-character limit.
    id: str = Field(min_length=1, max_length=69)
    title: Localized
    topic: Localized
    paragraphs: list[Localized] = Field(min_length=2, max_length=12)
    vocabulary_ids: list[str] = Field(min_length=1, max_length=30)
    question: StoryQuestion


class StageLibrary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=1, le=1)
    stage_id: str
    review_status: str = Field(pattern="^unreviewed$")
    vocabulary: list[LibraryWord] = Field(min_length=500)
    stories: list[LibraryStory] = Field(min_length=100)

    @model_validator(mode="after")
    def consistent_bank(self):
        if self.stage_id not in STAGE_IDS:
            raise ValueError("unknown library stage")
        word_ids = [item.id for item in self.vocabulary]
        terms = [normalise(item.term) for item in self.vocabulary]
        story_ids = [item.id for item in self.stories]
        if not all(terms):
            raise ValueError("blank vocabulary term")
        if len(set(word_ids)) != len(word_ids) or len(set(terms)) != len(terms):
            raise ValueError("duplicate vocabulary IDs or terms in a stage")
        if len(set(story_ids)) != len(story_ids):
            raise ValueError("duplicate story IDs")
        texts = [normalise(" ".join(p.nl for p in item.paragraphs)) for item in self.stories]
        if len(set(texts)) != len(texts):
            raise ValueError("duplicate Dutch stories within a stage")
        covered: set[str] = set()
        for story in self.stories:
            targets = set(story.vocabulary_ids)
            if len(targets) != len(story.vocabulary_ids) or not targets.issubset(word_ids):
                raise ValueError("invalid story vocabulary references")
            covered.update(targets)
        if covered != set(word_ids):
            raise ValueError("every vocabulary entry needs a Story Time connection")
        for value in self.vocabulary:
            for copy in (value.topic, value.meaning, value.example):
                if not all(text.strip() for text in (copy.nl, copy.en, copy.fa)):
                    raise ValueError("blank vocabulary translation")
        for story in self.stories:
            for copy in [story.title, story.topic, *story.paragraphs, story.question.prompt,
                         story.question.explanation, *story.question.options]:
                if not all(text.strip() for text in (copy.nl, copy.en, copy.fa)):
                    raise ValueError("blank story translation")
        return self


def normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@lru_cache(maxsize=16)
def _read(path: str, modified: int) -> StageLibrary:
    return StageLibrary.model_validate_json(Path(path).read_text(encoding="utf-8"))


def library_for(stage_id: str) -> StageLibrary:
    if stage_id not in STAGE_IDS:
        raise CurriculumError("learning stage not found", 404)
    path = CONTENT_DIR / "library" / f"{stage_id}.json"
    bank = _read(str(path), path.stat().st_mtime_ns)
    if bank.stage_id != stage_id:
        raise ValueError("library file does not match its requested stage")
    return bank


def validate_all_libraries() -> list[StageLibrary]:
    return [library_for(stage_id) for stage_id in STAGE_IDS]


def matches(item, query: str, topic: str) -> bool:
    if topic and item.topic.nl != topic:
        return False
    if not query:
        return True
    values = [item.topic.nl, item.topic.en, item.topic.fa]
    if isinstance(item, LibraryWord):
        values += [item.term, item.meaning.nl, item.meaning.en, item.meaning.fa,
                   item.example.nl, item.example.en, item.example.fa]
    else:
        values += [item.title.nl, item.title.en, item.title.fa]
        values += [text for p in item.paragraphs for text in (p.nl, p.en, p.fa)]
    return normalise(query) in normalise(" ".join(values))


def summary(bank: StageLibrary) -> dict:
    words = Counter(w.topic.nl for w in bank.vocabulary)
    stories = Counter(s.topic.nl for s in bank.stories)
    labels = {item.topic.nl: item.topic.model_dump() for item in [*bank.vocabulary, *bank.stories]}
    return {"stage_id": bank.stage_id, "review_status": bank.review_status,
            "vocabulary_count": len(bank.vocabulary), "story_count": len(bank.stories),
            "topics": [{"key": name, "label": labels[name], "vocabulary_count": words[name],
                        "story_count": stories[name]} for name in sorted(labels)]}


def vocabulary_page(bank: StageLibrary, *, query: str = "", topic: str = "", offset: int = 0, limit: int = 20):
    items = [item for item in bank.vocabulary if matches(item, query, topic)]
    return {"total": len(items), "offset": offset, "limit": limit,
            "items": [item.model_dump() for item in items[offset:offset + limit]]}


def story_page(bank: StageLibrary, *, query: str = "", topic: str = "", offset: int = 0, limit: int = 12):
    items = [item for item in bank.stories if matches(item, query, topic)]
    return {"total": len(items), "offset": offset, "limit": limit,
            "items": [{"id": item.id, "title": item.title.model_dump(), "topic": item.topic.model_dump(),
                       "preview": item.paragraphs[0].model_dump(), "paragraph_count": len(item.paragraphs),
                       "word_count": len(" ".join(p.nl for p in item.paragraphs).split()),
                       "vocabulary_ids": item.vocabulary_ids} for item in items[offset:offset + limit]]}


def story_detail(bank: StageLibrary, story_id: str):
    story = next((item for item in bank.stories if item.id == story_id), None)
    if story is None:
        raise CurriculumError("story not found", 404)
    data = story.model_dump()
    data["vocabulary"] = [item.model_dump() for item in bank.vocabulary if item.id in story.vocabulary_ids]
    data["question"]["id"] = story.id + "-understand"
    # Practice questions are deliberately visible; final-assessment answers remain separate.
    Question.model_validate(data["question"])
    return data
