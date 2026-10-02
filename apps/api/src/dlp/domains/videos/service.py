"""Video lessons: a presenter video at the learner's level about a topic they chose.

Flow
----
1. `request_video` stores the wish (level, topic, form) and queues the `video_script` job.
2. The job asks the chat model for a scene script, validates it with the story validator (Dutch, length and
   sentence complexity per level, vocabulary coverage, questions provable from the text), retries once with
   the validator's feedback, then hands the scenes to the configured renderer and queues `video_render`.
3. `video_render` polls the renderer; when the file is ready it pulls the subtitle track out as timed cues,
   remuxes for progressive playback, stores the file in blob storage and marks the lesson `ready`.
4. Watching, answering and saving words are ordinary code paths that award points for the day.

Every paid step is reserved against the usage counters before it runs and settled afterwards: model calls
and tokens for the writer, seconds of video for the renderer (billed per second by the avatar service).
"""
from __future__ import annotations

import logging
import random
import tempfile
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dlp.config import Settings, get_settings
from dlp.db.base import utcnow
from dlp.domains.curriculum import topics as topic_bank
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.identity.models import Learner
from dlp.domains.jobs import service as jobs
from dlp.domains.stories import service as stories
from dlp.domains.stories import today, vocab
from dlp.domains.stories.bible import StageProfile, profile_for
from dlp.domains.stories.validator import ValidationResult, feedback_text, validate_draft
from dlp.domains.usage import service as usage
from dlp.domains.videos import media
from dlp.domains.videos.models import VideoLesson
from dlp.domains.videos.prompts import SCRIPT_VERSION, script_messages
from dlp.domains.videos.schemas import KIND_LABELS, VideoScript
from dlp.providers.base import ProviderError, VideoRequest, VideoScene
from dlp.providers.chat_openai_compatible import schema_instruction
from dlp.providers.registry import Providers, get_providers

log = logging.getLogger(__name__)

WRITER_BASE_OUTPUT_TOKENS = 1500   # plus four tokens per word: three languages per scene
WORDS_PER_SECOND = 2.3             # a neural nl-BE voice at normal rate, including the pauses between scenes
MAX_PENDING = 2
MAX_RENDER_POLLS = 90
POINTS = {"watch": 10, "answer": 3}
RENDER_POLL_SECONDS = {"azure-avatar": 20.0}  # others finish at once; the job loop's own interval paces them


class VideoError(CurriculumError):
    """Same shape as the curriculum error so the routes share one handler."""


# --- profile and estimates --------------------------------------------------------------------------------

def words_for_seconds(seconds: int, scene_count: int) -> int:
    """How many spoken words it takes to fill `seconds`, pauses between scenes included."""
    return max(1, int((seconds - 2 - scene_count * 0.7) * WORDS_PER_SECOND) + 1)


def video_profile(stage_id: str, max_seconds: int, min_seconds: int = 20) -> StageProfile:
    """The stage profile, bounded to what fits a short video: between ~min_seconds and ~max_seconds of speech
    (a video shorter than twenty seconds is not a lesson), in 3-6 scenes."""
    profile = profile_for(stage_id)
    ceiling = max(60, int(max_seconds * WORDS_PER_SECOND * 0.9))
    floor = words_for_seconds(min_seconds, 3)
    max_words = max(min(profile.max_words, ceiling), floor + 20)
    min_words = max(floor, min(profile.min_words, max(40, int(max_words * 0.55))))
    return replace(profile, min_paragraphs=3, max_paragraphs=6, min_words=min_words, max_words=max_words)


def estimate_seconds(word_count: int, scene_count: int) -> int:
    return int(word_count / WORDS_PER_SECOND + scene_count * 0.7 + 2)


def levels() -> list[dict]:
    return [{"id": stage, "label": profile_for(stage).label} for stage in STAGE_IDS]


# --- requests ----------------------------------------------------------------------------------------------

def _pending(session: Session, learner_id: uuid.UUID) -> list[VideoLesson]:
    return list(session.scalars(select(VideoLesson).where(
        VideoLesson.learner_id == learner_id, VideoLesson.status.in_(("queued", "writing", "rendering")))
        .order_by(VideoLesson.created_at)))


def _pick_topic(stage_id: str, seed: str) -> tuple[str, str]:
    bank = topic_bank.topics_for(stage_id)
    topic = bank.topics[random.Random(seed).randrange(len(bank.topics))]
    return topic.id, topic.title.nl


def request_video(session: Session, learner: Learner, *, stage_id: str, topic: str, kind: str,
                  request_id: str) -> VideoLesson:
    if stage_id not in STAGE_IDS:
        raise VideoError("learning stage not found", 404)
    if kind not in KIND_LABELS:
        raise VideoError("unknown video form", 422)
    existing = session.scalar(select(VideoLesson).where(VideoLesson.learner_id == learner.id,
                                                        VideoLesson.checks["request_id"].astext == request_id))
    if existing is not None:
        return existing
    if len(_pending(session, learner.id)) >= MAX_PENDING:
        raise VideoError("two videos are already being made; watch one first", 409)
    topic = " ".join(topic.split())[:160]
    topic_id, title = ("", "")
    if not topic:
        topic_id, title = _pick_topic(stage_id, request_id)
        topic = title
    lesson = VideoLesson(learner_id=learner.id, stage_id=stage_id, kind=kind, topic=topic, topic_id=topic_id,
                         status="queued", checks={"request_id": request_id})
    session.add(lesson)
    session.flush()
    jobs.enqueue(session, "video_script", {"video_id": str(lesson.id)},
                 idempotency_key=f"video-script:{lesson.id.hex}", max_attempts=2)
    return lesson


# --- the script job ----------------------------------------------------------------------------------------

def _reload(session: Session, video_id: uuid.UUID) -> VideoLesson | None:
    return session.scalar(select(VideoLesson).where(VideoLesson.id == video_id).with_for_update()
                          .execution_options(populate_existing=True))


def _store_script(lesson: VideoLesson, script: VideoScript, result: ValidationResult, provider: str, model: str) -> None:
    lesson.title = script.title
    lesson.scenes = [{"nl": nl, "en": en, "fa": fa, "keyword": keyword} for nl, en, fa, keyword in
                     zip(script.paragraphs, script.paragraphs_en, script.paragraphs_fa, script.keywords, strict=True)]
    lesson.glossary = [item.model_dump() for item in script.glossary]
    lesson.questions = [item.model_dump() for item in script.questions]
    lesson.word_count = result.metrics.get("word_count", 0)
    lesson.checks = {**lesson.checks, **result.as_dict()}
    lesson.provider = provider
    lesson.model = model
    lesson.prompt_version = SCRIPT_VERSION


def check_script(script: VideoScript, profile: StageProfile, allowed: frozenset[str],
                 min_seconds: int = 20) -> ValidationResult:
    """The story checks plus what a video adds: every scene needs its translations and key word, and the
    spoken script must fill at least `min_seconds`."""
    result = validate_draft(script, profile, allowed_vocabulary=allowed, cast_names=frozenset())
    counts = {len(script.paragraphs), len(script.paragraphs_en), len(script.paragraphs_fa), len(script.keywords)}
    if len(counts) != 1:
        result.hard.append(f"scene_count_mismatch: {len(script.paragraphs)} scenes, {len(script.paragraphs_en)} English, "
                           f"{len(script.paragraphs_fa)} Persian, {len(script.keywords)} keywords")
        result.ok = False
    seconds = estimate_seconds(result.metrics.get("word_count", 0), len(script.paragraphs))
    if seconds < min_seconds:
        result.hard.append(f"video_too_short: ongeveer {seconds} seconden gesproken (minstens {min_seconds}). "
                           f"Schrijf minstens {words_for_seconds(min_seconds, len(script.paragraphs))} woorden: voeg een "
                           "scène met twee of drie zinnen toe.")
        result.ok = False
    result.metrics["estimated_seconds"] = seconds
    return result


def _write(session: Session, lesson: VideoLesson, settings: Settings, providers: Providers) -> str:
    """Write and validate the script; returns the outcome code ('ok' when the script was stored)."""
    profile = video_profile(lesson.stage_id, settings.video_max_seconds, settings.video_min_seconds)
    saved = stories.saved_word_keys(session, lesson.learner_id)
    stage_words = stories.stage_vocabulary(lesson.stage_id)
    rng = random.Random(f"{lesson.id}")
    known = saved[:60] + rng.sample(stage_words, min(len(stage_words), 140))
    candidates = [w for w in stage_words if w not in set(saved)]
    rng.shuffle(candidates)
    allowed = stories.allowed_vocabulary(session, lesson.learner_id, lesson.stage_id)
    chat = providers.chat_strong
    target_seconds = estimate_seconds((profile.min_words + profile.max_words) // 2, 4)
    messages = script_messages(profile=profile, kind=lesson.kind, topic=lesson.topic, known_words=known,
                               candidate_words=candidates[:40], target_seconds=target_seconds)
    best: tuple[VideoScript, ValidationResult] | None = None
    outcome = "quality"
    max_output = WRITER_BASE_OUTPUT_TOKENS + 4 * profile.max_words
    video_id = lesson.id
    for _attempt in range(2):
        estimate = (sum(len(m.content) for m in messages) + len(schema_instruction(VideoScript))) // 3 + max_output
        call_id = f"video-{lesson.id.hex}-{lesson.attempts}"
        calls = tokens_reservation = None
        try:
            calls = usage.reserve(session, settings, lesson.learner_id, "model_calls", 1, call_id)
            tokens_reservation = usage.reserve(session, settings, lesson.learner_id, "tokens", estimate, call_id)
        except usage.UsageLimitExceeded:
            if calls:
                usage.release(session, calls.id)
            if best is None:
                outcome = "allowance"
            break
        session.commit()  # the reservation is durable before the paid call
        lesson = _reload(session, video_id)  # type: ignore[assignment]
        if lesson is None or lesson.status != "writing":
            usage.release(session, calls.id)
            usage.release(session, tokens_reservation.id)
            return "obsolete"
        lesson.attempts += 1
        try:
            result = chat.complete(messages, schema=VideoScript, max_output_tokens=max_output, temperature=0.7,
                                   prompt_version=SCRIPT_VERSION, request_id=call_id)
        except ProviderError:
            usage.commit(session, calls.id, 1)
            usage.commit(session, tokens_reservation.id, estimate)
            outcome = "provider"
            break
        usage.commit(session, calls.id, 1)
        usage.commit(session, tokens_reservation.id, result.total_tokens)
        if not isinstance(result.parsed, VideoScript):
            outcome = "provider"
            break
        check = check_script(result.parsed, profile, allowed, settings.video_min_seconds)
        better = best is None or (check.ok and not best[1].ok) or (
            check.ok == best[1].ok and len(check.warnings) < len(best[1].warnings))
        if better:
            best = (result.parsed, check)
        outcome = "ok" if best[1].ok else "quality"
        if not check.needs_retry:
            break
        messages = script_messages(profile=profile, kind=lesson.kind, topic=lesson.topic, known_words=known,
                                   candidate_words=candidates[:40], target_seconds=target_seconds,
                                   feedback=feedback_text(check, profile))
    if outcome == "ok" and best is not None:
        _store_script(lesson, best[0], best[1], chat.name, chat.model)
    elif best is not None:
        lesson.checks = {**lesson.checks, **best[1].as_dict()}
    return outcome


def _start_render(session: Session, lesson: VideoLesson, settings: Settings, providers: Providers) -> str:
    """Reserve the seconds, hand the scenes to the renderer and queue the first poll; an outcome code."""
    renderer = providers.video
    seconds = estimate_seconds(lesson.word_count or sum(len(s["nl"].split()) for s in lesson.scenes), len(lesson.scenes))
    if seconds > settings.video_max_seconds:
        lesson.checks = {**lesson.checks, "estimated_seconds": seconds}
        return "too_long"
    call_id = f"video-render-{lesson.id.hex}-{uuid.uuid4().hex[:10]}"
    try:
        reservation = usage.reserve(session, settings, lesson.learner_id, "video_seconds", seconds, call_id)
    except usage.UsageLimitExceeded:
        return "allowance_video"
    lesson.checks = {**lesson.checks, "video_reservation": str(reservation.id), "estimated_seconds": seconds}
    session.commit()
    fresh = _reload(session, lesson.id)
    if fresh is None or fresh.status != "writing":
        usage.release(session, reservation.id)
        return "obsolete"
    lesson = fresh
    request = VideoRequest(scenes=[VideoScene(text=s["nl"], keyword=s.get("keyword", "")) for s in lesson.scenes],
                           title=lesson.title, voice=renderer.voice)
    try:
        job_id = renderer.start(request, request_id=call_id)
    except ProviderError as exc:
        log.warning("video render could not start: %s", exc)
        usage.release(session, reservation.id)
        lesson.checks = {**lesson.checks, "render_error": str(exc)[:200]}
        lesson.checks.pop("video_reservation", None)
        return "render"
    lesson.renderer = renderer.name
    lesson.render_job_id = job_id
    lesson.render_polls = 0
    lesson.voice = renderer.voice
    lesson.presenter = renderer.label
    lesson.status = "rendering"
    lesson.updated_at = utcnow()
    _queue_poll(session, lesson, delay=RENDER_POLL_SECONDS.get(renderer.name, 0.0))
    return "rendering"


def _queue_poll(session: Session, lesson: VideoLesson, *, delay: float) -> None:
    jobs.enqueue(session, "video_render", {"video_id": str(lesson.id)},
                 idempotency_key=f"video-render:{lesson.id.hex}:{lesson.render_job_id}:{lesson.render_polls}",
                 run_after=datetime.now(UTC) + timedelta(seconds=delay), max_attempts=3)


def write_and_render(session: Session, payload: dict, settings: Settings, providers: Providers) -> dict:
    video_id = uuid.UUID(payload["video_id"])
    lesson = session.scalar(select(VideoLesson).where(VideoLesson.id == video_id).with_for_update())
    if lesson is None:
        return {"status": "missing"}
    if lesson.status == "writing":
        # A previous worker claimed this lesson and disappeared mid-call; never repeat an uncertain paid call.
        lesson.status, lesson.error_code = "failed", "interrupted"
        return {"status": lesson.status}
    if lesson.status != "queued":
        return {"status": lesson.status}
    if settings.chat_provider == "azure" and not settings.paid_usage_enabled:
        lesson.status, lesson.error_code = "failed", "paid_not_approved"
        return {"status": lesson.status}
    lesson.status = "writing"
    lesson.updated_at = utcnow()
    session.commit()
    lesson = _reload(session, video_id)  # type: ignore[assignment]
    if lesson is None or lesson.status != "writing":
        return {"status": "obsolete"}

    outcome = "ok" if lesson.scenes else _write(session, lesson, settings, providers)
    if outcome == "obsolete":
        return {"status": "obsolete"}
    session.flush()
    lesson = _reload(session, video_id)  # type: ignore[assignment]
    assert lesson is not None
    if outcome == "ok":
        outcome = _start_render(session, lesson, settings, providers)
        if outcome == "obsolete":
            return {"status": "obsolete"}
        session.flush()
        lesson = _reload(session, video_id)  # type: ignore[assignment]
        assert lesson is not None
    if outcome != "rendering":
        lesson.status, lesson.error_code = "failed", outcome
    lesson.updated_at = utcnow()
    return {"status": lesson.status, "outcome": outcome, "attempts": lesson.attempts}


@jobs.registry.register("video_script")
def video_script_job(session: Session, payload: dict) -> dict:
    return write_and_render(session, payload, get_settings(), get_providers())


# --- the render job ----------------------------------------------------------------------------------------

def _settle_reservation(session: Session, lesson: VideoLesson, seconds: float | None) -> None:
    """Commit the measured seconds, or release the reservation when nothing was rendered."""
    token = (lesson.checks or {}).get("video_reservation")
    if not token:
        return
    try:
        reservation_id = uuid.UUID(str(token))
    except ValueError:
        return
    if seconds is None:
        usage.release(session, reservation_id)
    else:
        usage.commit(session, reservation_id, max(float(seconds), 0.0))
    lesson.checks = {k: v for k, v in lesson.checks.items() if k != "video_reservation"}


def _fail_render(session: Session, lesson: VideoLesson, providers: Providers, code: str, detail: str = "") -> dict:
    _settle_reservation(session, lesson, None)
    if lesson.render_job_id:
        providers.video.cleanup(lesson.render_job_id)
    lesson.status, lesson.error_code = "failed", code
    if detail:
        lesson.checks = {**lesson.checks, "render_error": detail[:200]}
    lesson.updated_at = utcnow()
    return {"status": "failed", "outcome": code}


def poll_render(session: Session, payload: dict, settings: Settings, providers: Providers) -> dict:
    video_id = uuid.UUID(payload["video_id"])
    lesson = _reload(session, video_id)
    if lesson is None:
        return {"status": "missing"}
    if lesson.status != "rendering":
        return {"status": lesson.status}
    renderer = providers.video
    if lesson.renderer and lesson.renderer != renderer.name:
        return _fail_render(session, lesson, providers, "render", f"renderer changed from {lesson.renderer} to {renderer.name}")
    try:
        state = renderer.status(lesson.render_job_id)
    except ProviderError as exc:
        state = None
        log.info("render status unavailable for %s: %s", lesson.id, exc)
    if state is None or state.state in ("pending", "running"):
        lesson.render_polls += 1
        waited = (datetime.now(UTC) - lesson.updated_at).total_seconds() if lesson.updated_at else 0.0
        if lesson.render_polls > MAX_RENDER_POLLS or waited > settings.video_render_timeout_seconds:
            return _fail_render(session, lesson, providers, "render_timeout")
        _queue_poll(session, lesson, delay=RENDER_POLL_SECONDS.get(renderer.name, 0.0))
        return {"status": "rendering", "polls": lesson.render_polls}
    if state.state == "failed":
        return _fail_render(session, lesson, providers, "render", state.detail)

    with tempfile.TemporaryDirectory(prefix="dlp-video-") as scratch:
        folder = Path(scratch)
        raw = folder / "raw.mp4"
        try:
            renderer.fetch(lesson.render_job_id, raw)
            final, cues, duration = media.finalize(raw, folder, [s["nl"] for s in lesson.scenes],
                                                   timeout=settings.ffmpeg_timeout_seconds * 6,
                                                   memory_limit_mb=settings.ffmpeg_memory_limit_mb)
            data = final.read_bytes()
            key = f"learner-video/{lesson.id.hex}.mp4"
            providers.blob.put(key, data, content_type="video/mp4")
        except ProviderError as exc:
            return _fail_render(session, lesson, providers, "render", str(exc))
        except Exception as exc:  # noqa: BLE001 - ffmpeg trouble ends this lesson, never the job loop
            log.warning("finalising video %s failed: %s", lesson.id, exc)
            return _fail_render(session, lesson, providers, "render", f"{exc.__class__.__name__}")
    if duration <= 0 and state.duration_ms:
        duration = round(state.duration_ms / 1000, 3)
    lesson.media_key = key
    lesson.media_bytes = len(data)
    lesson.duration_seconds = duration
    lesson.cues = cues
    _settle_reservation(session, lesson, duration)
    renderer.cleanup(lesson.render_job_id)
    lesson.status, lesson.error_code = "ready", ""
    lesson.ready_at = utcnow()
    lesson.updated_at = utcnow()
    return {"status": "ready", "seconds": duration, "cues": len(cues)}


@jobs.registry.register("video_render")
def video_render_job(session: Session, payload: dict) -> dict:
    return poll_render(session, payload, get_settings(), get_providers())


# --- learner-facing views ----------------------------------------------------------------------------------

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
    rows = session.scalars(select(VideoLesson).where(VideoLesson.learner_id == learner.id)
                           .order_by(VideoLesson.created_at.desc()).limit(limit))
    series = stories.ensure_series(session, learner)
    return {"items": [video_view(row, full=False) for row in rows], "levels": levels(),
            "kinds": [{"id": k, "label": v} for k, v in KIND_LABELS.items()], "default_stage": series.stage_id,
            "renderer": {"name": providers.video.name, "label": providers.video.label, "voice": providers.video.voice},
            "min_seconds": settings.video_min_seconds, "max_seconds": settings.video_max_seconds, "max_pending": MAX_PENDING}


def today_summary(session: Session, learner_id: uuid.UUID) -> dict:
    ready = session.scalar(select(VideoLesson).where(VideoLesson.learner_id == learner_id, VideoLesson.status == "ready",
                                                     VideoLesson.watched_at.is_(None))
                           .order_by(VideoLesson.ready_at.desc()).limit(1))
    pending = session.scalar(select(func.count()).select_from(VideoLesson).where(
        VideoLesson.learner_id == learner_id, VideoLesson.status.in_(("queued", "writing", "rendering")))) or 0
    return {"ready": video_view(ready, full=False) if ready else None, "pending": int(pending)}


# --- learner actions ---------------------------------------------------------------------------------------

def mark_watched(session: Session, learner: Learner, lesson: VideoLesson) -> dict:
    if lesson.status != "ready":
        raise VideoError("this video is not ready yet", 409)
    if lesson.watched_at is None:
        lesson.watched_at = utcnow()
        today.add_points(session, learner.id, points=POINTS["watch"], videos_watched=1)
    return video_view(lesson)


def answer_questions(session: Session, learner: Learner, lesson: VideoLesson, *, request_id: str,
                     answers: dict[str, int]) -> dict:
    if lesson.status != "ready":
        raise VideoError("this video is not ready yet", 409)
    state = dict(lesson.answers or {})
    if state.get("chosen") is not None:
        if state.get("request_id") != request_id:
            raise VideoError("the questions of this video were already answered", 409)
        return video_view(lesson)
    chosen = {str(i): answers.get(str(i)) for i in range(len(lesson.questions))}
    if any(value is None for value in chosen.values()):
        raise VideoError("answer every question", 422)
    correct = sum(1 for i, question in enumerate(lesson.questions) if chosen[str(i)] == question["answer_index"])
    state.update({"chosen": chosen, "correct": correct, "request_id": request_id, "answered_at": utcnow().isoformat()})
    lesson.answers = state
    if lesson.watched_at is None:
        lesson.watched_at = utcnow()
        today.add_points(session, learner.id, points=POINTS["watch"], videos_watched=1)
    if correct:
        today.add_points(session, learner.id, points=POINTS["answer"] * correct, questions_correct=correct)
    return video_view(lesson)


def rate(session: Session, learner: Learner, lesson: VideoLesson, rating: int) -> dict:
    lesson.rating = rating
    return video_view(lesson)


def save_word(session: Session, learner: Learner, lesson: VideoLesson, term: str) -> dict:
    wanted = vocab.key_for(term)
    entry = next((g for g in lesson.glossary if vocab.key_for(g["term"]) == wanted), None)
    if entry is None:
        raise vocab.VocabError("that word is not in this video's glossary", 404)
    item, created = vocab.save_word(session, learner, term=entry["term"], meaning_en=entry["meaning_en"],
                                    meaning_fa=entry["meaning_fa"], example=entry["example"], source_kind="video",
                                    source_id=str(lesson.id))
    return {"item": vocab.item_view(item), "created": created}


def retry_failed(session: Session, learner: Learner, lesson: VideoLesson) -> dict:
    if lesson.status != "failed":
        raise VideoError("only a failed video can be retried", 409)
    if lesson.error_code == "paid_not_approved":
        raise VideoError("paid usage is not approved for this environment", 409)
    if lesson.error_code in ("quality", "provider", "allowance", "interrupted"):
        lesson.scenes, lesson.glossary, lesson.questions, lesson.word_count = [], [], [], 0
    lesson.status, lesson.error_code = "queued", ""
    lesson.render_job_id, lesson.render_polls = "", 0
    lesson.updated_at = utcnow()
    jobs.enqueue(session, "video_script", {"video_id": str(lesson.id)},
                 idempotency_key=f"video-script:{lesson.id.hex}:retry:{lesson.attempts}:{utcnow().timestamp():.0f}",
                 max_attempts=2)
    return video_view(lesson, full=False)


def media_for(lesson: VideoLesson) -> tuple[str, int]:
    if lesson.status != "ready" or not lesson.media_key:
        raise VideoError("this video is not ready yet", 409)
    return lesson.media_key, lesson.media_bytes


def subtitles(lesson: VideoLesson) -> str:
    if lesson.status != "ready":
        raise VideoError("this video is not ready yet", 409)
    return media.vtt_for(lesson.cues)
