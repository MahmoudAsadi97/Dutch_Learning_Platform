"""The learner profile: ensure, view, update, set the stage. Free of story imports; orchestration that
touches the serial lives in onboarding.py so the two domains never import each other in a cycle."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.curriculum.service import passed_stages
from dlp.domains.identity.models import Learner
from dlp.domains.profile.models import LearnerProfile
from dlp.domains.profile.schemas import ProfileUpdate
from dlp.domains.stories.models import StorySeries


def starting_stage(session: Session, learner_id: uuid.UUID) -> str:
    """The first stage the learner has not passed; the pre-A1 bridge is skipped for a fresh learner."""
    passed = passed_stages(session, learner_id)
    first_open = next((stage for stage in STAGE_IDS if stage not in passed), STAGE_IDS[-1])
    return "a1" if first_open == "pre-a1" else first_open


def get(session: Session, learner_id: uuid.UUID) -> LearnerProfile | None:
    return session.scalar(select(LearnerProfile).where(LearnerProfile.learner_id == learner_id))


def _seed_stage(session: Session, learner_id: uuid.UUID) -> str:
    """A learner who already reads the serial keeps its level; anyone else starts at the first open stage."""
    serial = session.scalar(select(StorySeries.stage_id).where(StorySeries.learner_id == learner_id))
    return serial if serial in STAGE_IDS else starting_stage(session, learner_id)


def ensure(session: Session, learner: Learner) -> LearnerProfile:
    """One row per learner. Several first-visit requests may race; the winner inserts, the rest read it."""
    profile = get(session, learner.id)
    if profile is None:
        session.execute(
            insert(LearnerProfile)
            .values(learner_id=learner.id, stage_id=_seed_stage(session, learner.id),
                    created_at=utcnow(), updated_at=utcnow())
            .on_conflict_do_nothing()
        )
        profile = get(session, learner.id)
        assert profile is not None
    return profile


def suggested_stage(session: Session, profile: LearnerProfile) -> str | None:
    """A higher stage the learner has earned by passing checks, offered but never applied automatically."""
    passed = passed_stages(session, profile.learner_id)
    first_open = next((stage for stage in STAGE_IDS if stage not in passed), STAGE_IDS[-1])
    if STAGE_IDS.index(first_open) > STAGE_IDS.index(profile.stage_id):
        return first_open
    return None


def view(session: Session, learner: Learner, profile: LearnerProfile) -> dict:
    return {
        "learner": {"email": learner.email, "display_name": learner.display_name},
        "profile": {
            "stage_id": profile.stage_id,
            "daily_goal_points": profile.daily_goal_points,
            "support_mode": profile.support_mode,
            "gloss_mode": profile.gloss_mode,
            "stated_goal": profile.stated_goal,
            "onboarded_at": profile.onboarded_at.isoformat() if profile.onboarded_at else None,
            "suggested_stage_id": suggested_stage(session, profile),
        },
        "features": dict(profile.features or {}),
    }


def _mirror_support_language(learner: Learner, support_mode: str | None) -> None:
    if support_mode:
        learner.support_language = "fa" if "fa" in support_mode else "en"


def update(session: Session, learner: Learner, body: ProfileUpdate) -> LearnerProfile:
    profile = ensure(session, learner)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(profile, field, value)
    if "support_mode" in changes:
        _mirror_support_language(learner, changes["support_mode"])
    profile.updated_at = utcnow()
    session.flush()
    return profile


def set_stage(session: Session, learner: Learner, stage_id: str) -> LearnerProfile:
    if stage_id not in STAGE_IDS:
        raise ValueError("unknown learning stage")
    profile = ensure(session, learner)
    profile.stage_id = stage_id
    profile.updated_at = utcnow()
    session.flush()
    return profile


def reset(session: Session, learner: Learner) -> LearnerProfile:
    """Back to the defaults with onboarding undone; used by the browser tests, never in production."""
    profile = ensure(session, learner)
    profile.stage_id = starting_stage(session, learner.id)
    profile.daily_goal_points = 20
    profile.support_mode = None
    profile.gloss_mode = "auto"
    profile.stated_goal = ""
    profile.onboarded_at = None
    profile.updated_at = utcnow()
    session.flush()
    return profile
