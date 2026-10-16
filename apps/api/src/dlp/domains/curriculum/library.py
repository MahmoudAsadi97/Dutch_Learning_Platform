"""Versioned, original practice banks. Browsing never creates assessment credit."""
from __future__ import annotations

import json
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import supplements, word_usage
from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question
from dlp.domains.curriculum.service import CurriculumError


class WordForm(BaseModel):
    """An authored example of a form, never a guessed conjugation."""
    model_config = ConfigDict(extra="forbid")
    label: Localized
    text: Localized


class WordContext(BaseModel):
    """One use of a word in a specific situation, with a transfer invitation."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    setting: Localized
    sentence: Localized
    production_prompt: Localized
    structure: Literal["present", "past", "future", "modal", "conditional", "comparison",
                       "register", "noun_phrase", "adjective", "other"]


class LibraryWord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    term: str = Field(min_length=1, max_length=180)
    topic: Localized
    meaning: Localized
    example: Localized
    part_of_speech: Literal["noun", "verb", "adjective", "adverb", "expression", "other"] | None = None
    article: Literal["de", "het"] | None = None
    plural: str | None = Field(default=None, min_length=1, max_length=180)
    forms: list[WordForm] = Field(default_factory=list, max_length=8)
    contexts: list[WordContext] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def meaningful_usage(self):
        if self.article is not None and self.part_of_speech != "noun":
            raise ValueError("only a noun can have an article")
        if self.plural is not None and self.part_of_speech != "noun":
            raise ValueError("only a noun can have a plural")
        if len({item.id for item in self.contexts}) != len(self.contexts):
            raise ValueError("word contexts need unique IDs")
        texts = [normalise(item.sentence.nl) for item in self.contexts]
        if len(texts) != len(set(texts)):
            raise ValueError("word contexts must contain different Dutch examples")
        copies = [copy for item in self.forms for copy in (item.label, item.text)]
        copies += [copy for item in self.contexts for copy in (item.setting, item.sentence, item.production_prompt)]
        if any(not all(text.strip() for text in (copy.nl, copy.en, copy.fa)) for copy in copies):
            raise ValueError("word usage needs three nonblank language versions")
        return self


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
    genre: Localized | None = None
    paragraphs: list[Localized] = Field(min_length=2, max_length=12)
    lines: list[Localized] | None = Field(default=None, min_length=8, max_length=12)
    topic_id: str | None = Field(default=None, max_length=60, pattern=r"^[a-z0-9-]+$")
    vocabulary_ids: list[str] = Field(min_length=1, max_length=30)
    question: StoryQuestion

    @model_validator(mode="after")
    def parallel_narrative(self):
        if self.lines is not None:
            for language in ("nl", "en", "fa"):
                line_text = normalise(" ".join(getattr(line, language) for line in self.lines))
                paragraph_text = normalise(" ".join(getattr(p, language) for p in self.paragraphs))
                if line_text != paragraph_text:
                    raise ValueError("authored story lines must match their paragraphs in every language")
                if any(not getattr(line, language).strip() for line in self.lines):
                    raise ValueError("authored story lines require parallel translations")
            if any(len(line.nl) > 600 for line in self.lines):
                raise ValueError("authored story lines must fit sentence playback")
        return self


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
def _read(path: str, modified: int, supplement_modified: int = 0, usage_modified: int = 0) -> StageLibrary:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    root = Path(path).parent.parent
    return StageLibrary.model_validate(word_usage.enrich(supplements.merge_bank(data, root, "library"), root))


def library_for(stage_id: str) -> StageLibrary:
    if stage_id not in STAGE_IDS:
        raise CurriculumError("learning stage not found", 404)
    path = CONTENT_DIR / "library" / f"{stage_id}.json"
    bank = _read(str(path), path.stat().st_mtime_ns, supplements.stamp(CONTENT_DIR, stage_id),
                 word_usage.stamp(CONTENT_DIR, stage_id))
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
            "authored_story_count": sum(story.lines is not None for story in bank.stories),
            "target_story_count": 200,
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
                       "genre": item.genre.model_dump() if item.genre else None,
                       "preview": item.paragraphs[0].model_dump(), "paragraph_count": len(item.paragraphs),
                       "line_count": len(item.lines) if item.lines else None,
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
