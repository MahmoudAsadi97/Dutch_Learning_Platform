"""The learner's own profile: level, daily goal, support language, onboarding state and feature switches."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.profile import onboarding, service
from dlp.domains.profile.schemas import MeView, OnboardingBody, OnboardingView, ProfileUpdate

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=MeView)
def me(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)) -> dict:
    profile = service.ensure(session, ctx.learner)
    return service.view(session, ctx.learner, profile)


@router.patch("", response_model=MeView)
def update_me(body: ProfileUpdate, ctx: RequestContext = Depends(context_dep),
              session: Session = Depends(get_session)) -> dict:
    profile = onboarding.update(session, ctx.learner, body)
    return service.view(session, ctx.learner, profile)


@router.post("/onboarding", response_model=OnboardingView)
def onboard(body: OnboardingBody, ctx: RequestContext = Depends(context_dep),
            session: Session = Depends(get_session)) -> dict:
    return onboarding.complete(session, ctx.learner, body)


@router.post("/reset", response_model=MeView)
def reset_me(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
             session: Session = Depends(get_session)) -> dict:
    """Undo onboarding and return to the defaults. Browser tests use it; production never serves it."""
    if settings.app_env == "production":
        raise HTTPException(status_code=404, detail="not found")
    profile = onboarding.reset(session, ctx.learner)
    return service.view(session, ctx.learner, profile)
