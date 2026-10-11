from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner

# how stale "last seen" may get: writing it on every request would make every read a write and queue one
# learner's parallel requests on the learner row
LAST_SEEN_EVERY = timedelta(minutes=10)


def get_or_create_learner(session: Session, principal: Principal) -> Learner:
    learner = session.scalar(select(Learner).where(Learner.subject == principal.subject))
    if learner is None:
        learner = session.scalar(select(Learner).where(Learner.email == principal.email))
    if learner is None:
        # The dashboard loads several endpoints at once on a first visit. A uniqueness race is normal,
        # not a server error: let the winner insert, then read that same learner after it commits.
        session.execute(insert(Learner).values(
            subject=principal.subject, email=principal.email, display_name=principal.name,
            identity_provider=principal.identity_provider,
        ).on_conflict_do_nothing())
        learner = session.scalar(select(Learner).where(Learner.subject == principal.subject))
        if learner is None:
            learner = session.scalar(select(Learner).where(Learner.email == principal.email))
        assert learner is not None
    else:
        now = utcnow()
        if learner.last_seen_at is None or now - learner.last_seen_at >= LAST_SEEN_EVERY:
            learner.last_seen_at = now
        if principal.name and learner.display_name != principal.name:
            learner.display_name = principal.name
    return learner


def lock_learner(session: Session, learner_id) -> None:
    """Serializes one learner's writes that change several of their rows (the profile and the story series), so
    two of them never take those row locks in opposite orders. Taken first, before any other row lock; FOR NO KEY
    UPDATE does not block the key-share locks that foreign-key checks take on the learner row."""
    session.execute(select(Learner.id).where(Learner.id == learner_id).with_for_update(key_share=True)).one()
