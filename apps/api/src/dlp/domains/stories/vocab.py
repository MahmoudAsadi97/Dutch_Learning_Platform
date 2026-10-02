"""The personal word bank with spaced repetition (SM-2).

A word enters the bank only when the learner saves it (from a story glossary, the library or by hand).
Reviews reschedule it; a lapse brings it back within the same session. Intervals are a scheduling aid,
not a measurement of mastery.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.identity.models import Learner
from dlp.domains.stories import today
from dlp.domains.stories.models import StoryEpisode, VocabItem
from dlp.domains.stories.validator import lemma_key, normalise

GRADES = {"again": 1, "hard": 3, "good": 4, "easy": 5}
LEARNED_INTERVAL_DAYS = 21
REVIEW_POINTS = 1


class VocabError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def key_for(term: str) -> str:
    return (lemma_key(term) or normalise(term))[:120]


def item_view(item: VocabItem, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    return {"id": str(item.id), "term": item.term, "meaning_en": item.meaning_en, "meaning_fa": item.meaning_fa,
            "example": item.example, "source_kind": item.source_kind, "source_id": item.source_id,
            "ease": round(item.ease, 2), "interval_days": item.interval_days, "repetitions": item.repetitions,
            "lapses": item.lapses, "due_at": item.due_at.isoformat(), "due": item.due_at <= now,
            "learned": item.interval_days >= LEARNED_INTERVAL_DAYS, "last_grade": item.last_grade,
            "created_at": item.created_at.isoformat()}


def save_word(session: Session, learner: Learner, *, term: str, meaning_en: str = "", meaning_fa: str = "",
              example: str = "", source_kind: str = "manual", source_id: str = "") -> tuple[VocabItem, bool]:
    key = key_for(term)
    if not key:
        raise VocabError("a word is required", 422)
    existing = session.scalar(select(VocabItem).where(VocabItem.learner_id == learner.id, VocabItem.key == key))
    if existing is not None:
        changed = False
        for field, value in (("meaning_en", meaning_en), ("meaning_fa", meaning_fa), ("example", example)):
            if value and not getattr(existing, field):
                setattr(existing, field, value)
                changed = True
        return existing, changed
    item = VocabItem(learner_id=learner.id, key=key, term=" ".join(term.split())[:120], meaning_en=meaning_en[:300],
                     meaning_fa=meaning_fa[:300], example=example[:400], source_kind=source_kind,
                     source_id=source_id[:80], due_at=utcnow())
    session.add(item)
    session.flush()
    return item, True


def save_from_episode(session: Session, learner: Learner, episode: StoryEpisode, term: str) -> tuple[VocabItem, bool]:
    wanted = key_for(term)
    entry = next((g for g in episode.glossary if key_for(g["term"]) == wanted), None)
    if entry is None:
        raise VocabError("that word is not in this episode's glossary", 404)
    return save_word(session, learner, term=entry["term"], meaning_en=entry["meaning_en"], meaning_fa=entry["meaning_fa"],
                     example=entry["example"], source_kind="story", source_id=str(episode.id))


def remove_word(session: Session, learner: Learner, item_id: uuid.UUID) -> None:
    item = session.scalar(select(VocabItem).where(VocabItem.id == item_id, VocabItem.learner_id == learner.id))
    if item is None:
        raise VocabError("word not found", 404)
    session.delete(item)


def schedule(item: VocabItem, grade: str, *, now: datetime | None = None) -> None:
    """SM-2 with one adjustment: a failed card returns in ten minutes instead of tomorrow."""
    now = now or datetime.now(UTC)
    quality = GRADES[grade]
    item.repetitions = item.repetitions or 0
    item.interval_days = item.interval_days or 0
    item.lapses = item.lapses or 0
    item.ease = item.ease or 2.5
    if quality < 3:
        item.repetitions = 0
        item.interval_days = 0
        item.lapses += 1
        item.due_at = now + timedelta(minutes=10)
    else:
        item.repetitions += 1
        if item.repetitions == 1:
            item.interval_days = 1
        elif item.repetitions == 2:
            item.interval_days = 6 if quality >= 4 else 3
        else:
            factor = item.ease * (0.8 if quality == 3 else 1.3 if quality == 5 else 1.0)
            item.interval_days = max(item.interval_days + 1, round(item.interval_days * factor))
        item.ease = max(1.3, item.ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        item.due_at = now + timedelta(days=item.interval_days)
    item.last_grade = quality
    item.reviewed_at = now


def review(session: Session, learner: Learner, item_id: uuid.UUID, *, grade: str, request_id: str) -> dict:
    if grade not in GRADES:
        raise VocabError("unknown grade", 422)
    item = session.scalar(select(VocabItem).where(VocabItem.id == item_id, VocabItem.learner_id == learner.id)
                          .with_for_update())
    if item is None:
        raise VocabError("word not found", 404)
    if item.last_request_id == request_id:
        return item_view(item)
    item.last_request_id = request_id
    schedule(item, grade)
    today.add_points(session, learner.id, points=REVIEW_POINTS, words_reviewed=1)
    return item_view(item)


def due_items(session: Session, learner: Learner, *, limit: int = 20, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    rows = list(session.scalars(select(VocabItem).where(VocabItem.learner_id == learner.id, VocabItem.due_at <= now)
                                .order_by(VocabItem.due_at).limit(limit)))
    return {"items": [item_view(row, now=now) for row in rows], **stats(session, learner, now=now)}


def all_items(session: Session, learner: Learner, *, limit: int = 500) -> dict:
    now = datetime.now(UTC)
    rows = list(session.scalars(select(VocabItem).where(VocabItem.learner_id == learner.id)
                                .order_by(VocabItem.created_at.desc()).limit(limit)))
    return {"items": [item_view(row, now=now) for row in rows], **stats(session, learner, now=now)}


def stats(session: Session, learner: Learner, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    base = select(func.count()).select_from(VocabItem).where(VocabItem.learner_id == learner.id)
    total = int(session.scalar(base) or 0)
    due = int(session.scalar(base.where(VocabItem.due_at <= now)) or 0)
    learned = int(session.scalar(base.where(VocabItem.interval_days >= LEARNED_INTERVAL_DAYS)) or 0)
    new = int(session.scalar(base.where(VocabItem.repetitions == 0, VocabItem.lapses == 0)) or 0)
    return {"total": total, "due_count": due, "learned_count": learned, "new_count": new}
