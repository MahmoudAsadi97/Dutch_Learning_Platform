"""First-run onboarding: store the choices once, sync the serial's level, and queue episode one so the
first visit to Vandaag does not wait for the writer."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.activity.service import retarget_today
from dlp.domains.identity.models import Learner
from dlp.domains.identity.service import lock_learner
from dlp.domains.profile import service
from dlp.domains.profile.models import LearnerProfile
from dlp.domains.profile.schemas import OnboardingBody, ProfileUpdate
from dlp.domains.stories import service as stories
from dlp.domains.stories.models import StorySeries


def reset(session: Session, learner: Learner) -> LearnerProfile:
    """Undo onboarding (browser tests only); an existing serial follows the profile back to its start."""
    lock_learner(session, learner.id)
    profile = service.reset(session, learner)
    series = session.scalar(select(StorySeries).where(StorySeries.learner_id == learner.id))
    if series is not None and series.stage_id != profile.stage_id:
        stories.set_level(session, learner, profile.stage_id)
    return profile


def update(session: Session, learner: Learner, body: ProfileUpdate) -> LearnerProfile:
    """A profile change; a new level also moves the serial, so the next episode is written at it. The learner is
    locked first: this writes the profile, then the series, and a level change from the stories writes them the
    other way round."""
    lock_learner(session, learner.id)
    profile = service.update(session, learner, body)
    if "stage_id" in body.model_fields_set and body.stage_id is not None:
        stories.set_level(session, learner, body.stage_id)
    if "daily_goal_points" in body.model_fields_set:
        retarget_today(session, learner.id, profile.daily_goal_points)
    return profile


def complete(session: Session, learner: Learner, body: OnboardingBody) -> dict:
    lock_learner(session, learner.id)
    profile = service.ensure(session, learner)
    if profile.onboarded_at is not None:
        return {"already_onboarded": True, **service.view(session, learner, profile), "episode": None}
    profile.support_mode = body.support_mode
    profile.stage_id = body.stage_id
    profile.daily_goal_points = body.daily_goal_points
    profile.stated_goal = body.stated_goal
    profile.onboarded_at = utcnow()
    profile.updated_at = utcnow()
    learner.support_language = "nl" if body.support_mode == "nl" else "en"
    session.flush()
    retarget_today(session, learner.id, profile.daily_goal_points)
    stories.set_level(session, learner, body.stage_id)
    episode = stories.ensure_buffer(session, learner)
    if episode is not None:
        episode = stories.restage_queued(session, episode, body.stage_id)
    return {
        "already_onboarded": False,
        **service.view(session, learner, profile),
        "episode": stories.episode_view(episode, full=False) if episode is not None else None,
    }
