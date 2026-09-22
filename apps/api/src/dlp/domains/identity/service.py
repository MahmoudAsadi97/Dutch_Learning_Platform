from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner


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
        learner.last_seen_at = utcnow()
        if principal.name and learner.display_name != principal.name:
            learner.display_name = principal.name
    return learner
