from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class ExerciseSession(Base):
    """One practice session: items generated once from a seed at creation and stored, then answered one by one.

    Idempotent on (learner_id, request_id); `params` holds what the session was created with (and its
    fingerprint, so a reused request id with other parameters is refused). Items are never regenerated from
    the seed on read, so a content change cannot alter a session in progress."""

    __tablename__ = "exercise_sessions"
    __table_args__ = (
        UniqueConstraint("learner_id", "request_id", name="uq_exercise_sessions_learner_request"),
        Index("ix_exercise_sessions_learner_status", "learner_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # stage_skill | while_you_wait (more later)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(60), nullable=False, default="", server_default="")
    skill: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="")
    focus: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="")  # words, ...
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(20), nullable=False)
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="active")  # active|finished|abandoned
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExerciseItem(Base):
    """One item of a session. `prompt` is exactly what the browser may see before answering; `key` (the
    correct option, glosses, explanation) never leaves the server until the item is answered, and never
    appears in the export. `attempts` holds at most two answers, each with the response it got, so a
    repeated request replays it."""

    __tablename__ = "exercise_items"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_exercise_items_session_position"),
        Index("ix_exercise_items_learner_ref", "learner_id", "ref"),
        Index("ix_exercise_items_learner_word", "learner_id", "word"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise_sessions.id", ondelete="CASCADE"),
                                                  nullable=False)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="")
    # what it practises: word:<library id>, question:<question id>, intro:<stage>
    ref: Mapped[str] = mapped_column(String(120), nullable=False)
    # the word across stages (stories.vocab.key_for), '' when the item is not about one word
    word: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    prompt: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    key: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    attempts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    first_outcome: Mapped[str | None] = mapped_column(String(12), nullable=True)
    closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hint_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    points_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LearnerMistake(Base):
    """A first-attempt miss on something the learner had met before, in the one taxonomy (`taxonomy.py`).

    The columns are the shared superset: exercises fill source, kind, category, given and expected;
    writing, conversation and tutor (later phases) add `quote` (the learner's own words). `assessed` is false
    for judgements no real check made (fixture providers), which are never shown as mistakes. Resolution
    (a later Brussels day) arrives with "repeat your mistakes" (roadmap 5.2)."""

    __tablename__ = "learner_mistakes"
    __table_args__ = (
        UniqueConstraint("learner_id", "source", "source_id", name="uq_learner_mistakes_learner_source"),
        Index("ix_learner_mistakes_learner_created", "learner_id", "created_at"),
        Index("ix_learner_mistakes_learner_category", "learner_id", "category"),
        Index("ix_learner_mistakes_learner_ref", "learner_id", "ref"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # exercise | writing | conversation | tutor
    source_id: Mapped[str] = mapped_column(String(80), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="")
    kind: Mapped[str] = mapped_column(String(24), nullable=False, default="", server_default="")
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(10), nullable=False)
    ref: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    lemma: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    given: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    expected: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    quote: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    assessed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    request_id: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class WordSuggestion(Base):
    """A library word the learner missed and may want in their word bank. Only the learner saves a word
    (D-19): a suggestion is an offer, kept per word across stages (`key`), counted per miss."""

    __tablename__ = "word_suggestions"
    __table_args__ = (UniqueConstraint("learner_id", "key", name="uq_word_suggestions_learner_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    term: Mapped[str] = mapped_column(String(120), nullable=False)
    meaning_en: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    meaning_fa: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    example: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="library", server_default="library")
    source_id: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    reason: Mapped[str] = mapped_column(String(20), nullable=False)  # missed | topic
    miss_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="open", server_default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
