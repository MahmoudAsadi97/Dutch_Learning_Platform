"""Stories, the word bank and the daily plan. Reads are free; a deliberate POST may queue a model call."""
from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.speech.audio import AudioError
from dlp.domains.speech.service import transcribe_upload
from dlp.domains.stories import service, today, vocab
from dlp.domains.stories.bible import PROFILES
from dlp.domains.stories.schemas import (
    AnswerBody,
    ChooseBody,
    LevelBody,
    RateBody,
    RequestEpisodeBody,
    ReviewBody,
    SaveWordBody,
    TranslateBody,
)
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.domains.videos import service as videos
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

router = APIRouter(tags=["stories"])


def _run(operation: Callable):
    try:
        return operation()
    except (CurriculumError, vocab.VocabError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except AudioError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    except UsageLimitExceeded:
        return JSONResponse(status_code=429, content={"detail": "Your practice allowance is used up. Try again later."})
    except ProviderError:
        return JSONResponse(status_code=503, content={"detail": "The language service is temporarily unavailable. "
                                                                 "Your progress is saved; try again in a moment."})


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc


# --- today ------------------------------------------------------------------------------------------------

@router.get("/today")
def today_plan(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    def build():
        episode = service.today_episode(session, ctx.learner)
        words = vocab.due_items(session, ctx.learner, limit=5)
        run = today.streak(session, ctx.learner.id)
        current = episode["episode"]
        if current and current["status"] == "ready" and not current["read_at"]:
            next_step = "read"
        elif episode["awaiting_choice"]:
            next_step = "choose"
        elif words["due_count"]:
            next_step = "review"
        elif current and current["status"] in ("queued", "generating"):
            next_step = "wait"
        else:
            next_step = "explore"
        return {
            "date": today.local_today().isoformat(), "streak": run,
            "goal": {"target": today.DAILY_GOAL, "points": run["today_points"],
                     "met": run["today_points"] >= today.DAILY_GOAL},
            "series": episode["series"], "episode": current, "failed": episode["failed"],
            "awaiting_choice": episode["awaiting_choice"],
            "words": {"due_count": words["due_count"], "total": words["total"], "learned_count": words["learned_count"],
                      "new_count": words["new_count"], "preview": words["items"][:3]},
            "next_step": next_step, "recent_days": today.recent_days(session, ctx.learner.id),
            "levels": [{"id": p.stage_id, "label": p.label} for p in PROFILES.values()],
            "videos": videos.today_summary(session, ctx.learner.id),
        }
    return _run(build)


# --- stories ----------------------------------------------------------------------------------------------

@router.get("/stories")
def stories_list(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.library(session, ctx.learner))


@router.post("/stories/episodes", status_code=202)
def stories_request(body: RequestEpisodeBody, ctx: RequestContext = Depends(context_dep),
                    session: Session = Depends(get_session)):
    return _run(lambda: service.episode_view(service.queue_episode(
        session, ctx.learner, theme=body.theme, theme_source="learner", request_id=body.request_id), full=False))


@router.post("/stories/level")
def stories_level(body: LevelBody, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.set_level(session, ctx.learner, body.stage_id))


@router.get("/stories/episodes/{episode_id}")
def episode_get(episode_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.episode_view(service.get_episode(session, ctx.learner, _uuid(episode_id))))


@router.post("/stories/episodes/{episode_id}/read")
def episode_read(episode_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.mark_read(session, ctx.learner,
                                          service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True)))


@router.post("/stories/episodes/{episode_id}/answers")
def episode_answers(episode_id: str, body: AnswerBody, ctx: RequestContext = Depends(context_dep),
                    session: Session = Depends(get_session)):
    return _run(lambda: service.answer_questions(
        session, ctx.learner, service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True),
        request_id=body.request_id, answers=body.answers))


@router.post("/stories/episodes/{episode_id}/choice")
def episode_choice(episode_id: str, body: ChooseBody, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)):
    return _run(lambda: service.choose(session, ctx.learner,
                                       service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True), body.choice))


@router.post("/stories/episodes/{episode_id}/rating")
def episode_rating(episode_id: str, body: RateBody, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)):
    return _run(lambda: service.rate(session, ctx.learner,
                                     service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True), body.rating))


@router.post("/stories/episodes/{episode_id}/retry", status_code=202)
def episode_retry(episode_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.retry_failed(session, ctx.learner,
                                             service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True)))


@router.post("/stories/episodes/{episode_id}/translate")
def episode_translate(episode_id: str, body: TranslateBody, ctx: RequestContext = Depends(context_dep),
                      settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
                      session: Session = Depends(get_session)):
    return _run(lambda: service.translate_paragraph(
        session, settings, providers, ctx.learner, service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True),
        paragraph_index=body.paragraph_index, request_id=body.request_id))


@router.post("/stories/episodes/{episode_id}/words")
def episode_save_word(episode_id: str, body: SaveWordBody, ctx: RequestContext = Depends(context_dep),
                      session: Session = Depends(get_session)):
    def save():
        episode = service.get_episode(session, ctx.learner, _uuid(episode_id))
        item, created = vocab.save_from_episode(session, ctx.learner, episode, body.term)
        return {"item": vocab.item_view(item), "created": created}
    return _run(save)


@router.post("/stories/episodes/{episode_id}/read-aloud")
def episode_read_aloud(episode_id: str, paragraph_index: int = Form(ge=0, le=7), audio: UploadFile = File(...),
                       ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                       providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    def run():
        episode = service.get_episode(session, ctx.learner, _uuid(episode_id), lock=True)
        if episode.status != "ready":
            raise CurriculumError("this episode is not ready yet", 409)
        if paragraph_index >= len(episode.paragraphs):
            raise CurriculumError("paragraph not found", 404)
        outcome = transcribe_upload(session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id,
                                    upload_bytes=audio.file.read(), upload_filename=audio.filename or "recording",
                                    stt=providers.stt, blob=providers.blob, keep_recording=False)
        result = service.read_aloud_result(episode, paragraph_index=paragraph_index, transcript=outcome.transcript.text)
        return service.record_read_aloud(session, ctx.learner, episode, result)
    return _run(run)


# --- words --------------------------------------------------------------------------------------------------

@router.get("/words")
def words_list(due: bool = Query(default=False), limit: int = Query(default=20, ge=1, le=500),
               ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: vocab.due_items(session, ctx.learner, limit=limit) if due
                else vocab.all_items(session, ctx.learner, limit=limit))


@router.post("/words", status_code=201)
def words_save(body: SaveWordBody, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    def save():
        item, created = vocab.save_word(session, ctx.learner, term=body.term, meaning_en=body.meaning_en,
                                        meaning_fa=body.meaning_fa, example=body.example, source_kind=body.source_kind,
                                        source_id=body.source_id)
        return {"item": vocab.item_view(item), "created": created}
    return _run(save)


@router.post("/words/{item_id}/review")
def words_review(item_id: str, body: ReviewBody, ctx: RequestContext = Depends(context_dep),
                 session: Session = Depends(get_session)):
    return _run(lambda: vocab.review(session, ctx.learner, _uuid(item_id), grade=body.grade, request_id=body.request_id))


@router.delete("/words/{item_id}", status_code=204)
def words_delete(item_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    _run(lambda: vocab.remove_word(session, ctx.learner, _uuid(item_id)))
    return None
