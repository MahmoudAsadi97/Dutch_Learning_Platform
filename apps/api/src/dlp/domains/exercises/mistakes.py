"""What the learner has met, the mistakes worth repeating, and the words worth offering for the word bank.

A word is met once an earlier session closed an item about it, or once the learner saved it. A miss on a
word not met before is a first encounter, not a mistake: it writes no row (red team, step 3.3).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, union
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.exercises.models import ExerciseItem, LearnerMistake, WordSuggestion
from dlp.domains.exercises.taxonomy import TAXONOMY_VERSION, Category
from dlp.domains.stories.models import VocabItem


def met_words(session: Session, learner_id: uuid.UUID) -> frozenset[str]:
    practised = select(ExerciseItem.word).where(ExerciseItem.learner_id == learner_id, ExerciseItem.closed.is_(True),
                                                ExerciseItem.word != "")
    saved = select(VocabItem.key).where(VocabItem.learner_id == learner_id)
    return frozenset(session.scalars(union(practised, saved)))


def last_practised(session: Session, learner_id: uuid.UUID) -> dict[str, datetime]:
    rows = session.execute(select(ExerciseItem.word, func.max(ExerciseItem.answered_at))
                           .where(ExerciseItem.learner_id == learner_id, ExerciseItem.word != "",
                                  ExerciseItem.answered_at.is_not(None))
                           .group_by(ExerciseItem.word))
    return {word: at for word, at in rows}


def record_mistake(session: Session, *, learner_id: uuid.UUID, source: str, source_id: str, stage_id: str,
                   category: Category, skill: str = "", kind: str = "", ref: str = "", lemma: str = "",
                   given: str = "", expected: str = "", quote: str = "", assessed: bool = True,
                   request_id: str = "", detail: dict[str, Any] | None = None) -> None:
    """One row per source item; a retried request finds it and adds nothing."""
    session.execute(insert(LearnerMistake).values(
        id=uuid.uuid4(), learner_id=learner_id, source=source, source_id=source_id, stage_id=stage_id, skill=skill,
        kind=kind, category=category, taxonomy_version=TAXONOMY_VERSION, ref=ref[:120], lemma=lemma[:120],
        given=given[:300], expected=expected[:300], quote=quote[:200], assessed=assessed, request_id=request_id,
        detail=detail or {}, created_at=utcnow(),
    ).on_conflict_do_nothing(index_elements=["learner_id", "source", "source_id"]))


def suggest_words(session: Session, learner_id: uuid.UUID, words: list[tuple[str, dict[str, Any]]]) -> list[dict]:
    """Offer missed library words the learner has not saved: one suggestion per word, counted per miss. A
    suggestion the learner dismissed or saved keeps its status."""
    saved = set(session.scalars(select(VocabItem.key).where(VocabItem.learner_id == learner_id)))
    offered: dict[str, dict[str, Any]] = {}
    for key, card in words:
        if key and key not in saved and key not in offered:
            offered[key] = card
    for key, card in offered.items():
        session.execute(insert(WordSuggestion).values(
            id=uuid.uuid4(), learner_id=learner_id, key=key, term=card["term"][:120],
            meaning_en=card["meaning"]["en"][:300], meaning_fa=card["meaning"]["fa"][:300],
            example=card["example"]["nl"], source_kind="library", source_id=card["library_id"][:80], reason="missed",
            miss_count=1, status="open", created_at=utcnow(), updated_at=utcnow(),
        ).on_conflict_do_update(index_elements=["learner_id", "key"], set_={
            "miss_count": WordSuggestion.miss_count + 1, "updated_at": utcnow(),
        }))
    if not offered:
        return []
    rows = session.scalars(select(WordSuggestion).where(WordSuggestion.learner_id == learner_id,
                                                        WordSuggestion.key.in_(offered),
                                                        WordSuggestion.status == "open")
                           .execution_options(populate_existing=True))
    return [{"key": row.key, "term": row.term, "meaning_en": row.meaning_en, "meaning_fa": row.meaning_fa}
            for row in sorted(rows, key=lambda row: list(offered).index(row.key))]
