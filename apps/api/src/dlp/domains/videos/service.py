"""Read-only video archive and retirement handlers.

Video creation has been removed. Old records and files remain available to their owner without a
migration or a destructive cleanup. Every generation entry point is closed, including jobs already
queued before the upgrade; no model, synthesis or rendering adapter is called by these handlers.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.identity.models import Learner
from dlp.domains.jobs import service as jobs
from dlp.domains.stories.bible import profile_for
from dlp.domains.usage import service as usage
from dlp.domains.videos import media
from dlp.domains.videos.models import VideoLesson
from dlp.domains.videos.schemas import KIND_LABELS
from dlp.providers.registry import Providers

RETIRED_DETAIL = "Video creation has been retired. Use narrated stories instead."


class VideoError(CurriculumError):
    code = "video"


def levels() -> list[dict]:
    return [{"id": stage, "label": profile_for(stage).label} for stage in STAGE_IDS]


def request_video(session: Session, learner: Learner, *, stage_id: str, topic: str, kind: str,
                  request_id: str) -> VideoLesson:
    """Reject old clients before they create work or reserve paid usage."""
    raise VideoError(RETIRED_DETAIL, 410, params={"replacement_url": "/verhalen"})


def _settle_reservation(session: Session, lesson: VideoLesson, seconds: float | None) -> None:
    """Commit measured seconds; retain uncertain Azure work rather than refunding a failed render."""
    token = (lesson.checks or {}).get("video_reservation")
    if not token:
        return
    try:
        reservation_id = uuid.UUID(str(token))
    except ValueError:
        return
    checks = lesson.checks or {}
    # Before provenance was recorded, card lessons still stored the configured
    # voice. Azure's persisted Neural voice is an indicative conservative signal
    # of paid narration, not proof of an invoice. Old jobs must still be drained
    # before deploying a schema/runtime change.
    legacy_paid_narration = ("paid_render" not in checks and lesson.renderer == "scene-cards"
                             and lesson.voice.endswith("Neural"))
    paid = lesson.renderer == "azure-avatar" or bool(checks.get("paid_render")) or legacy_paid_narration
    if paid:
        # A fresh poll worker has no in-memory dispatch marker. The provenance
        # was persisted before rendering; both failed and successful paid work
        # settle independently of the lesson/status transaction.
        actual = float((lesson.checks or {}).get("estimated_seconds", 0)) if seconds is None else max(float(seconds), 0.0)
        usage.commit(session, reservation_id, actual, durable=True)
    elif seconds is None:
        usage.release(session, reservation_id)
    else:
        usage.commit(session, reservation_id, max(float(seconds), 0.0))
    lesson.checks = {k: v for k, v in lesson.checks.items() if k != "video_reservation"}


def retire_pending(session: Session, payload: dict) -> dict:
    """Drain pre-upgrade jobs without polling, retrying or dispatching a provider.

    A render already sent to a paid provider may already have been billed. Settle its persisted
    reservation conservatively; never release uncertain expenditure as if no request occurred.
    """
    video_id = uuid.UUID(payload["video_id"])
    lesson = session.scalar(select(VideoLesson).where(VideoLesson.id == video_id).with_for_update())
    if lesson is None:
        return {"status": "missing"}
    if lesson.status in ("queued", "writing", "rendering"):
        _settle_reservation(session, lesson, None)
        lesson.status, lesson.error_code = "failed", "retired"
        lesson.updated_at = utcnow()
    return {"status": lesson.status, "generation_enabled": False}


def write_and_render(session: Session, payload: dict, settings: Settings, providers: Providers) -> dict:
    return retire_pending(session, payload)


def poll_render(session: Session, payload: dict, settings: Settings, providers: Providers) -> dict:
    return retire_pending(session, payload)


@jobs.registry.register("video_script")
def video_script_job(session: Session, payload: dict) -> dict:
    return retire_pending(session, payload)


@jobs.registry.register("video_render")
def video_render_job(session: Session, payload: dict) -> dict:
    return retire_pending(session, payload)


def _question_view(index: int, question: dict, answered: dict | None) -> dict:
    view = {"index": index, "prompt": question["prompt"], "options": question["options"]}
    if answered is not None:
        view["answer_index"] = question["answer_index"]
        view["evidence"] = question["evidence"]
        chosen = answered.get(str(index))
        view["chosen"] = chosen
        view["correct"] = chosen == question["answer_index"]
    return view


def video_view(lesson: VideoLesson, *, full: bool = True) -> dict:
    answered = lesson.answers.get("chosen") if lesson.answers else None
    checks = lesson.checks or {}
    view = {
        "id": str(lesson.id), "stage_id": lesson.stage_id, "kind": lesson.kind,
        "kind_label": KIND_LABELS.get(lesson.kind, lesson.kind),
        "topic": lesson.topic, "topic_id": lesson.topic_id, "status": lesson.status, "error_code": lesson.error_code,
        "title": lesson.title, "word_count": lesson.word_count, "duration_seconds": lesson.duration_seconds,
        "presenter": lesson.presenter, "renderer": lesson.renderer, "attempts": lesson.attempts,
        "watched_at": lesson.watched_at.isoformat() if lesson.watched_at else None, "rating": lesson.rating,
        "created_at": lesson.created_at.isoformat(), "ready_at": lesson.ready_at.isoformat() if lesson.ready_at else None,
        "content_status": "generated", "warnings": list(checks.get("warnings", [])),
        "failure_reasons": [*checks.get("hard", []),
                            *([checks["render_error"]] if lesson.status == "failed" and checks.get("render_error") else [])],
        "scene_count": len(lesson.scenes),
    }
    if full and lesson.status == "ready":
        view.update({
            "scenes": lesson.scenes, "glossary": lesson.glossary, "cues": lesson.cues,
            "questions": [_question_view(i, q, answered) for i, q in enumerate(lesson.questions)],
            "answered": answered is not None, "provider": lesson.provider, "model": lesson.model, "voice": lesson.voice,
            "media_url": f"videos/{lesson.id}/media", "subtitles_url": f"videos/{lesson.id}/subtitles.vtt",
        })
    return view


def get_video(session: Session, learner: Learner, video_id: uuid.UUID, *, lock: bool = False) -> VideoLesson:
    statement = select(VideoLesson).where(VideoLesson.id == video_id, VideoLesson.learner_id == learner.id)
    if lock:
        statement = statement.with_for_update()
    lesson = session.scalar(statement)
    if lesson is None:
        raise VideoError("video not found", 404)
    return lesson


def library(session: Session, learner: Learner, settings: Settings, providers: Providers, *, limit: int = 60) -> dict:
    """Read-only historical records, kept for exports and existing bookmarks."""
    rows = session.scalars(select(VideoLesson).where(VideoLesson.learner_id == learner.id)
                           .order_by(VideoLesson.created_at.desc()).limit(limit))
    return {"items": [video_view(row, full=False) for row in rows], "levels": levels(),
            "kinds": [], "default_stage": "", "generation_enabled": False,
            "replacement_url": "/verhalen", "renderer": {"name": "disabled", "label": "retired", "voice": ""},
            "min_seconds": 0, "max_seconds": 0, "max_pending": 0}


def today_summary(session: Session, learner_id: uuid.UUID) -> dict:
    return {"ready": None, "pending": 0}


def retry_failed(session: Session, learner: Learner, lesson: VideoLesson) -> dict:
    """Historical failures cannot re-open a paid generation path."""
    raise VideoError(RETIRED_DETAIL, 410, params={"replacement_url": "/verhalen"})


def media_for(lesson: VideoLesson) -> tuple[str, int]:
    if lesson.status != "ready" or not lesson.media_key:
        raise VideoError("this video is not ready yet", 409, code="not_ready")
    return lesson.media_key, lesson.media_bytes


def subtitles(lesson: VideoLesson) -> str:
    if lesson.status != "ready":
        raise VideoError("this video is not ready yet", 409, code="not_ready")
    return media.vtt_for(lesson.cues)

