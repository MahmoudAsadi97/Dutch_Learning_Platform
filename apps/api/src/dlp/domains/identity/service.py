from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner


def get_or_create_learner(session: Session, principal: Principal) -> Learner:
    learner = session.scalar(select(Learner).where(Learner.subject == principal.subject))
    if learner is None:
        learner = session.scalar(select(Learner).where(Learner.email == principal.email))
    if learner is None:
        learner = Learner(
            subject=principal.subject,
            email=principal.email,
            display_name=principal.name,
            identity_provider=principal.identity_provider,
        )
        session.add(learner)
        session.flush()
    else:
        learner.last_seen_at = utcnow()
        if principal.name and learner.display_name != principal.name:
            learner.display_name = principal.name
    return learner
