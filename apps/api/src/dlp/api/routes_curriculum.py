from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.curriculum import service
from dlp.domains.curriculum.schemas import Skill, Test
from dlp.domains.speech.audio import AudioError
from dlp.domains.speech.service import synthesize_text
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


class PracticeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: Skill
    answers: dict[str, StrictInt] = Field(default_factory=dict, max_length=30)
    text: str = Field(default="", max_length=12000)
    audio_asset_id: uuid.UUID | None = None


class StartBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


class SubmitBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reading_answers: dict[str, StrictInt] = Field(max_length=30)
    listening_answers: dict[str, StrictInt] = Field(max_length=30)
    writing_text: str = Field(min_length=1, max_length=12000)
    speaking_asset_id: uuid.UUID


def _run(operation: Callable):
    try:
        return operation()
    except service.CurriculumError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except AudioError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    except UsageLimitExceeded:
        # Returning a response commits already completed billable work; it does not award a partial pass.
        return JSONResponse(status_code=429, content={"detail": "Your practice allowance is used up. Try again later."})
    except ProviderError:
        return JSONResponse(status_code=503, content={
            "detail": "The language service is temporarily unavailable. Your check has not been passed; please retry.",
        })
    except OperationalError as exc:
        if getattr(exc.orig, "sqlstate", "") == "55P03":
            raise HTTPException(status_code=409, detail="this response is already being processed; retry shortly") from exc
        raise


@router.get("")
def catalogue(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
              session: Session = Depends(get_session)):
    return _run(lambda: service.catalogue(session, ctx.learner.id, admin=service.is_admin(settings, ctx.principal.email),
                                          recording_max_seconds=settings.max_audio_seconds))


# Static 'attempts' routes deliberately precede the stage routes.
@router.get("/attempts/{attempt_id}")
def attempt_get(attempt_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
                settings: Settings = Depends(settings_dep), session: Session = Depends(get_session)):
    def operation():
        attempt = service.get_attempt(session, ctx.learner.id, attempt_id)
        service.require_access(session, ctx.learner.id, attempt.stage_id,
                               admin=service.is_admin(settings, ctx.principal.email))
        return service.attempt_view(attempt, recording_max_seconds=settings.max_audio_seconds)
    return _run(operation)


@router.post("/attempts/{attempt_id}/submit")
def attempt_submit(attempt_id: uuid.UUID, body: SubmitBody, ctx: RequestContext = Depends(context_dep),
                   settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
                   session: Session = Depends(get_session)):
    def operation():
        attempt = service.get_attempt(session, ctx.learner.id, attempt_id, lock=True)
        service.require_access(session, ctx.learner.id, attempt.stage_id,
                               admin=service.is_admin(settings, ctx.principal.email))
        return service.attempt_view(service.submit_attempt(
            session, settings, providers, learner_id=ctx.learner.id, attempt=attempt,
            submission=body.model_dump(mode="json"), request_id=ctx.request_id,
        ), recording_max_seconds=settings.max_audio_seconds)
    return _run(operation)


def _audio(text: str, part: int, ctx: RequestContext, settings: Settings, providers: Providers, session: Session):
    parts = service.audio_parts(text)
    if part >= len(parts):
        raise service.CurriculumError("listening part not found", 404)
    data, _, label = synthesize_text(
        session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id,
        text=parts[part], tts=providers.tts, blob=providers.blob,
    )
    return Response(content=data, media_type="audio/wav", headers={"X-Audio-Label": label, "Cache-Control": "no-store"})


@router.post("/attempts/{attempt_id}/listening")
def attempt_listening(attempt_id: uuid.UUID, part: int = Query(default=0, ge=0, le=100),
                      ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                      providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    def operation():
        attempt = service.get_attempt(session, ctx.learner.id, attempt_id)
        service.require_access(session, ctx.learner.id, attempt.stage_id,
                               admin=service.is_admin(settings, ctx.principal.email))
        return _audio(Test.model_validate(attempt.test_snapshot).listening.text.nl, part, ctx, settings, providers, session)
    return _run(operation)


@router.get("/{stage_id}")
def stage_get(stage_id: str, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
              session: Session = Depends(get_session)):
    def operation():
        admin = service.is_admin(settings, ctx.principal.email)
        stage = service.require_access(session, ctx.learner.id, stage_id, admin=admin)
        return service.stage_view(session, ctx.learner.id, stage, admin=admin, recording_max_seconds=settings.max_audio_seconds)
    return _run(operation)


@router.post("/{stage_id}/practice")
def practice(stage_id: str, body: PracticeBody, ctx: RequestContext = Depends(context_dep),
             settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
             session: Session = Depends(get_session)):
    def operation():
        stage = service.require_access(session, ctx.learner.id, stage_id,
                                       admin=service.is_admin(settings, ctx.principal.email))
        return service.save_practice(
            session, settings, providers, learner_id=ctx.learner.id, stage=stage, skill=body.skill,
            answers=body.answers, text=body.text, asset_id=body.audio_asset_id, request_id=ctx.request_id,
        )
    return _run(operation)


@router.post("/{stage_id}/test")
def test_start(stage_id: str, body: StartBody, ctx: RequestContext = Depends(context_dep),
               settings: Settings = Depends(settings_dep), session: Session = Depends(get_session)):
    def operation():
        admin = service.is_admin(settings, ctx.principal.email)
        stage = service.require_access(session, ctx.learner.id, stage_id, admin=admin)
        return service.attempt_view(service.start_attempt(session, ctx.learner.id, stage, body.request_id, admin=admin),
                                    recording_max_seconds=settings.max_audio_seconds)
    return _run(operation)


@router.post("/{stage_id}/listening")
def lesson_listening(stage_id: str, part: int = Query(default=0, ge=0, le=100),
                     ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                     providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    def operation():
        stage = service.require_access(session, ctx.learner.id, stage_id,
                                       admin=service.is_admin(settings, ctx.principal.email))
        return _audio(stage.lesson.listening.nl, part, ctx, settings, providers, session)
    return _run(operation)
