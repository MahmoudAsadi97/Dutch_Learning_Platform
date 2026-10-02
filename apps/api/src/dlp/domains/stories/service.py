"""The story engine: a continuing serial written ahead of the learner by a background job.

Flow
----
1. `today_episode` makes sure the learner has a series and at least one unread episode queued or ready.
2. The `story_episode` job calls the writer with the series memory, the learner's saved words and the stage
   vocabulary, validates the draft deterministically, retries once with the validator's feedback, and stores
   the episode as `ready` (or `failed`, with a reason the learner can act on).
3. Reading, answering, choosing and rating are ordinary code paths that award points for the day.
"""
from __future__ import annotations

import hashlib
import logging
import random
import uuid
from copy import deepcopy
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.config import Settings, get_settings
from dlp.db.base import utcnow
from dlp.domains.curriculum import service as curriculum
from dlp.domains.curriculum import topics as topic_bank
from dlp.domains.curriculum.library import library_for
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.identity.models import Learner
from dlp.domains.jobs import service as jobs
from dlp.domains.stories import today
from dlp.domains.stories.bible import DEFAULT_BIBLE, SERIES_TITLE, profile_for, stages_up_to
from dlp.domains.stories.models import StoryEpisode, StorySeries, VocabItem
from dlp.domains.stories.prompts import TRANSLATE_VERSION, WRITER_VERSION, translate_messages, writer_messages
from dlp.domains.stories.schemas import EpisodeDraft, Translation
from dlp.domains.stories.validator import ValidationResult, feedback_text, lemma_key, tokens, validate_draft
from dlp.domains.usage import service as usage
from dlp.providers.base import ProviderError
from dlp.providers.chat_openai_compatible import schema_instruction
from dlp.providers.registry import Providers, get_providers

log = logging.getLogger(__name__)

WRITER_BASE_OUTPUT_TOKENS = 1200  # plus three tokens per word of the stage's longest story
TRANSLATE_MAX_OUTPUT_TOKENS = 500
POINTS = {"read": 10, "answer": 3, "choose": 2, "read_aloud": 5}


class StoryError(curriculum.CurriculumError):
    """Same shape as the curriculum error so the routes can share one handler."""


# --- series ----------------------------------------------------------------------------------------------

def default_stage(session: Session, learner_id: uuid.UUID) -> str:
    passed = curriculum.passed_stages(session, learner_id)
    first_open = next((stage for stage in STAGE_IDS if stage not in passed), STAGE_IDS[-1])
    return "a1" if first_open == "pre-a1" else first_open


def ensure_series(session: Session, learner: Learner) -> StorySeries:
    series = session.scalar(select(StorySeries).where(StorySeries.learner_id == learner.id).with_for_update())
    if series is None:
        series = StorySeries(learner_id=learner.id, stage_id=default_stage(session, learner.id), title=SERIES_TITLE,
                             bible=deepcopy(DEFAULT_BIBLE), memory=[], episode_count=0)
        session.add(series)
        session.flush()
    return series


def set_level(session: Session, learner: Learner, stage_id: str) -> dict:
    if stage_id not in STAGE_IDS:
        raise StoryError("learning stage not found", 404)
    series = ensure_series(session, learner)
    series.stage_id = stage_id
    series.updated_at = utcnow()
    session.flush()
    return series_view(series)


def series_view(series: StorySeries) -> dict:
    return {"id": str(series.id), "title": series.title, "stage_id": series.stage_id,
            "episode_count": series.episode_count, "town": series.bible["setting"]["town"],
            "cast": [{"name": c["name"], "role": c["role"]} for c in series.bible["cast"]],
            "memory": [{"number": m["number"], "title": m.get("title", ""), "recap": m["recap"],
                        "choice": m.get("choice", "")} for m in series.memory[-6:]]}


# --- vocabulary context ----------------------------------------------------------------------------------

def saved_word_keys(session: Session, learner_id: uuid.UUID) -> list[str]:
    return list(session.scalars(select(VocabItem.key).where(VocabItem.learner_id == learner_id)
                                .order_by(VocabItem.created_at.desc()).limit(400)))


def stage_vocabulary(stage_id: str) -> list[str]:
    seen: dict[str, None] = {}
    for stage in stages_up_to(stage_id):
        for word in library_for(stage).vocabulary:
            seen.setdefault(lemma_key(word.term), None)
    return list(seen)


def allowed_vocabulary(session: Session, learner_id: uuid.UUID, stage_id: str) -> frozenset[str]:
    words = set(stage_vocabulary(stage_id)) | set(saved_word_keys(session, learner_id))
    return frozenset(w for key in words for w in key.split())


def pick_theme(stage_id: str, number: int, recent_topics: set[str]) -> tuple[str, str]:
    bank = topic_bank.topics_for(stage_id)
    order = list(range(len(bank.topics)))
    random.Random(f"{stage_id}:{number}").shuffle(order)
    for index in order:
        topic = bank.topics[index]
        if topic.id not in recent_topics:
            return topic.id, topic.title.nl
    topic = bank.topics[number % len(bank.topics)]
    return topic.id, topic.title.nl


# --- queueing --------------------------------------------------------------------------------------------

def _unread_episodes(session: Session, series: StorySeries) -> list[StoryEpisode]:
    return list(session.scalars(select(StoryEpisode).where(
        StoryEpisode.series_id == series.id, StoryEpisode.read_at.is_(None),
        StoryEpisode.status.in_(("queued", "generating", "ready")),
    ).order_by(StoryEpisode.number)))


def queue_episode(session: Session, learner: Learner, *, theme: str = "", theme_source: str = "auto",
                  request_id: str = "") -> StoryEpisode:
    series = ensure_series(session, learner)
    if request_id:
        existing = session.scalar(select(StoryEpisode).where(StoryEpisode.series_id == series.id,
                                                             StoryEpisode.checks["request_id"].astext == request_id))
        if existing is not None:
            return existing
    pending = [e for e in _unread_episodes(session, series) if e.status in ("queued", "generating")]
    if len(pending) >= 2:
        raise StoryError("two episodes are already being written; read one first", 409)
    number = series.episode_count + 1
    series.episode_count = number
    last_read = session.scalar(select(StoryEpisode).where(StoryEpisode.series_id == series.id,
                                                          StoryEpisode.read_at.is_not(None))
                               .order_by(StoryEpisode.number.desc()).limit(1))
    previous_choice = ""
    if last_read is not None and last_read.chosen_choice:
        previous_choice = next((c["label"] for c in last_read.choices if c["id"] == last_read.chosen_choice), "")
    recent_topics = set(session.scalars(select(StoryEpisode.topic_id).where(StoryEpisode.series_id == series.id)
                                        .order_by(StoryEpisode.number.desc()).limit(12)))
    topic_id, topic_title = pick_theme(series.stage_id, number, recent_topics)
    episode = StoryEpisode(
        learner_id=learner.id, series_id=series.id, number=number, stage_id=series.stage_id, status="queued",
        theme=(theme.strip()[:160] or topic_title), theme_source=("learner" if theme.strip() else theme_source),
        topic_id=topic_id, previous_choice=previous_choice, checks={"request_id": request_id},
    )
    session.add(episode)
    session.flush()
    jobs.enqueue(session, "story_episode", {"episode_id": str(episode.id)},
                 idempotency_key=f"story-episode:{episode.id.hex}", max_attempts=2)
    return episode


CHOICE_GRACE = timedelta(hours=12)


def awaiting_choice(session: Session, series: StorySeries) -> StoryEpisode | None:
    """The last read episode, while its choice is still open and recent enough to shape the next one."""
    last_read = session.scalar(select(StoryEpisode).where(StoryEpisode.series_id == series.id,
                                                          StoryEpisode.read_at.is_not(None))
                               .order_by(StoryEpisode.number.desc()).limit(1))
    if (last_read is not None and last_read.choices and not last_read.chosen_choice
            and last_read.read_at is not None and datetime.now(UTC) - last_read.read_at < CHOICE_GRACE):
        return last_read
    return None


def ensure_buffer(session: Session, learner: Learner) -> StoryEpisode | None:
    """Keep one unread episode queued or ready so the next visit never waits for the writer.

    While the reader still owes a choice for the last episode, nothing is queued: the choice must reach
    the writer. After twelve hours the serial continues without it."""
    series = ensure_series(session, learner)
    unread = _unread_episodes(session, series)
    if unread:
        return unread[0]
    if awaiting_choice(session, series) is not None:
        return None
    return queue_episode(session, learner)


# --- generation (job) ------------------------------------------------------------------------------------

def _memory_entry(episode: StoryEpisode) -> dict:
    return {"number": episode.number, "title": episode.title, "recap": episode.recap, "theme": episode.theme}


def _store_draft(episode: StoryEpisode, draft: EpisodeDraft, result: ValidationResult, provider: str, model: str) -> None:
    english = list(draft.paragraphs_en) + [""] * (len(draft.paragraphs) - len(draft.paragraphs_en))
    episode.title = draft.title
    episode.paragraphs = [{"nl": nl, "en": en} for nl, en in zip(draft.paragraphs, english, strict=False)]
    episode.glossary = [item.model_dump() for item in draft.glossary]
    episode.questions = [item.model_dump() for item in draft.questions]
    episode.choices = [item.model_dump() for item in draft.choices]
    episode.recap = draft.recap
    episode.mood = draft.mood[:30]
    episode.word_count = result.metrics.get("word_count", 0)
    episode.checks = {**episode.checks, **result.as_dict()}
    episode.provider = provider
    episode.model = model
    episode.prompt_version = WRITER_VERSION


def generate_episode(session: Session, payload: dict, settings: Settings, providers: Providers) -> dict:
    episode_id = uuid.UUID(payload["episode_id"])
    episode = session.scalar(select(StoryEpisode).where(StoryEpisode.id == episode_id).with_for_update())
    if episode is None:
        return {"status": "missing"}
    if episode.status == "generating":
        # A previous worker claimed this episode and disappeared mid-call; never repeat an uncertain paid call.
        episode.status, episode.error_code = "failed", "interrupted"
        return {"status": episode.status}
    if episode.status != "queued":
        return {"status": episode.status}
    if settings.chat_provider == "azure" and not settings.paid_usage_enabled:
        episode.status, episode.error_code = "failed", "paid_not_approved"
        return {"status": episode.status}
    series = session.get(StorySeries, episode.series_id)
    assert series is not None
    profile = profile_for(episode.stage_id)
    saved = saved_word_keys(session, episode.learner_id)
    stage_words = stage_vocabulary(episode.stage_id)
    rng = random.Random(f"{episode.id}")
    known = saved[:60] + rng.sample(stage_words, min(len(stage_words), 140))
    candidates = [w for w in stage_words if w not in set(saved)]
    rng.shuffle(candidates)
    allowed = allowed_vocabulary(session, episode.learner_id, episode.stage_id)
    cast_names = frozenset(c["name"] for c in series.bible["cast"])

    episode.status = "generating"
    episode.updated_at = utcnow()
    session.commit()
    episode = session.scalar(select(StoryEpisode).where(StoryEpisode.id == episode_id).with_for_update()
                             .execution_options(populate_existing=True))
    if episode is None or episode.status != "generating":
        return {"status": "obsolete"}

    chat = providers.chat_strong
    messages = writer_messages(profile=profile, bible=series.bible, memory=series.memory, known_words=known,
                               candidate_words=candidates[:40], theme=episode.theme,
                               previous_choice=episode.previous_choice, episode_number=episode.number)
    best: tuple[EpisodeDraft, ValidationResult] | None = None
    outcome = "quality"
    max_output = WRITER_BASE_OUTPUT_TOKENS + 3 * profile.max_words
    for _attempt in range(2):
        estimate = (sum(len(m.content) for m in messages) + len(schema_instruction(EpisodeDraft))) // 3 + max_output
        call_id = f"story-{episode.id.hex}-{episode.attempts}"
        calls = tokens_reservation = None
        try:
            calls = usage.reserve(session, settings, episode.learner_id, "model_calls", 1, call_id)
            tokens_reservation = usage.reserve(session, settings, episode.learner_id, "tokens", estimate, call_id)
        except usage.UsageLimitExceeded:
            if calls:
                usage.release(session, calls.id)
            if best is None:
                outcome = "allowance"
            break
        # The reservation is durable before the call: a crash mid-call must not refund uncertain work.
        session.commit()
        episode = session.scalar(select(StoryEpisode).where(StoryEpisode.id == episode_id).with_for_update()
                                 .execution_options(populate_existing=True))
        if episode is None or episode.status != "generating":
            usage.release(session, calls.id)
            usage.release(session, tokens_reservation.id)
            return {"status": "obsolete"}
        episode.attempts += 1
        try:
            result = chat.complete(messages, schema=EpisodeDraft, max_output_tokens=max_output,
                                   temperature=0.7, prompt_version=WRITER_VERSION, request_id=call_id)
        except ProviderError:
            # A timed-out call may have been billed: charge the estimate rather than refund it.
            usage.commit(session, calls.id, 1)
            usage.commit(session, tokens_reservation.id, estimate)
            outcome = "provider"
            break
        usage.commit(session, calls.id, 1)
        usage.commit(session, tokens_reservation.id, result.total_tokens)
        if not isinstance(result.parsed, EpisodeDraft):
            outcome = "provider"
            break
        check = validate_draft(result.parsed, profile, allowed_vocabulary=allowed, cast_names=cast_names)
        better = best is None or (check.ok and not best[1].ok) or (
            check.ok == best[1].ok and len(check.warnings) < len(best[1].warnings))
        if better:
            best = (result.parsed, check)
        outcome = "ok" if best[1].ok else "quality"
        if not check.needs_retry:
            break
        messages = writer_messages(profile=profile, bible=series.bible, memory=series.memory, known_words=known,
                                   candidate_words=candidates[:40], theme=episode.theme,
                                   previous_choice=episode.previous_choice, episode_number=episode.number,
                                   feedback=feedback_text(check, profile))
    if outcome == "ok" and best is not None:
        _store_draft(episode, best[0], best[1], chat.name, chat.model)
        episode.status, episode.error_code = "ready", ""
        series = session.get(StorySeries, series.id)
        assert series is not None
        series.memory = [*series.memory[-11:], _memory_entry(episode)]
        series.updated_at = utcnow()
    else:
        episode.status = "failed"
        episode.error_code = outcome
        if best is not None:
            episode.checks = {**episode.checks, **best[1].as_dict()}
    episode.updated_at = utcnow()
    return {"status": episode.status, "attempts": episode.attempts}


@jobs.registry.register("story_episode")
def story_episode_job(session: Session, payload: dict) -> dict:
    return generate_episode(session, payload, get_settings(), get_providers())


# --- learner-facing views --------------------------------------------------------------------------------

def _question_view(index: int, question: dict, answered: dict | None) -> dict:
    view = {"index": index, "prompt": question["prompt"], "options": question["options"]}
    if answered is not None:
        view["answer_index"] = question["answer_index"]
        view["evidence"] = question["evidence"]
        chosen = answered.get(str(index))
        view["chosen"] = chosen
        view["correct"] = chosen == question["answer_index"]
    return view


def episode_view(episode: StoryEpisode, *, full: bool = True) -> dict:
    answered = episode.answers.get("chosen") if episode.answers else None
    view = {
        "id": str(episode.id), "number": episode.number, "stage_id": episode.stage_id, "status": episode.status,
        "error_code": episode.error_code, "title": episode.title, "theme": episode.theme,
        "theme_source": episode.theme_source, "topic_id": episode.topic_id, "mood": episode.mood,
        "word_count": episode.word_count, "read_at": episode.read_at.isoformat() if episode.read_at else None,
        "rating": episode.rating, "chosen_choice": episode.chosen_choice, "created_at": episode.created_at.isoformat(),
        "content_status": "generated", "attempts": episode.attempts,
        "warnings": list((episode.checks or {}).get("warnings", [])),
        "failure_reasons": list((episode.checks or {}).get("hard", [])) if episode.status == "failed" else [],
    }
    if full and episode.status == "ready":
        view.update({
            "paragraphs": episode.paragraphs, "glossary": episode.glossary, "choices": episode.choices,
            "questions": [_question_view(i, q, answered) for i, q in enumerate(episode.questions)],
            "answered": answered is not None, "previous_choice": episode.previous_choice,
            "read_aloud": (episode.answers or {}).get("read_aloud", {}),
            "provider": episode.provider, "model": episode.model,
        })
    return view


def get_episode(session: Session, learner: Learner, episode_id: uuid.UUID, *, lock: bool = False) -> StoryEpisode:
    statement = select(StoryEpisode).where(StoryEpisode.id == episode_id, StoryEpisode.learner_id == learner.id)
    if lock:
        statement = statement.with_for_update()
    episode = session.scalar(statement)
    if episode is None:
        raise StoryError("episode not found", 404)
    return episode


def today_episode(session: Session, learner: Learner) -> dict:
    series = ensure_series(session, learner)
    current = ensure_buffer(session, learner)
    failed = session.scalar(select(StoryEpisode).where(StoryEpisode.series_id == series.id,
                                                       StoryEpisode.status == "failed", StoryEpisode.read_at.is_(None))
                            .order_by(StoryEpisode.number.desc()).limit(1))
    pending_choice = awaiting_choice(session, series) if current is None else None
    return {"series": series_view(series), "episode": episode_view(current) if current else None,
            "awaiting_choice": episode_view(pending_choice, full=False) if pending_choice else None,
            "failed": episode_view(failed, full=False) if failed else None}


def library(session: Session, learner: Learner, *, limit: int = 60) -> dict:
    series = ensure_series(session, learner)
    rows = session.scalars(select(StoryEpisode).where(StoryEpisode.series_id == series.id)
                           .order_by(StoryEpisode.number.desc()).limit(limit))
    return {"series": series_view(series), "items": [episode_view(row, full=False) for row in rows]}


# --- learner actions -------------------------------------------------------------------------------------

def mark_read(session: Session, learner: Learner, episode: StoryEpisode) -> dict:
    if episode.status != "ready":
        raise StoryError("this episode is not ready yet", 409)
    if episode.read_at is None:
        episode.read_at = utcnow()
        today.add_points(session, learner.id, points=POINTS["read"], episodes_read=1)
    return episode_view(episode)


def answer_questions(session: Session, learner: Learner, episode: StoryEpisode, *, request_id: str,
                     answers: dict[str, int]) -> dict:
    if episode.status != "ready":
        raise StoryError("this episode is not ready yet", 409)
    state = dict(episode.answers or {})
    if state.get("chosen") is not None:
        if state.get("request_id") != request_id:
            raise StoryError("the questions of this episode were already answered", 409)
        return episode_view(episode)
    chosen = {str(i): answers.get(str(i)) for i in range(len(episode.questions))}
    if any(value is None for value in chosen.values()):
        raise StoryError("answer every question", 422)
    correct = sum(1 for i, question in enumerate(episode.questions) if chosen[str(i)] == question["answer_index"])
    state.update({"chosen": chosen, "correct": correct, "request_id": request_id, "answered_at": utcnow().isoformat()})
    episode.answers = state
    if episode.read_at is None:
        episode.read_at = utcnow()
        today.add_points(session, learner.id, points=POINTS["read"], episodes_read=1)
    if correct:
        today.add_points(session, learner.id, points=POINTS["answer"] * correct, questions_correct=correct)
    return episode_view(episode)


def choose(session: Session, learner: Learner, episode: StoryEpisode, choice: str) -> dict:
    if episode.status != "ready":
        raise StoryError("this episode is not ready yet", 409)
    if choice not in {c["id"] for c in episode.choices}:
        raise StoryError("unknown choice", 422)
    first_choice = not episode.chosen_choice
    episode.chosen_choice = choice
    if episode.read_at is None:
        episode.read_at = utcnow()
        today.add_points(session, learner.id, points=POINTS["read"], episodes_read=1)
    if first_choice:
        today.add_points(session, learner.id, points=POINTS["choose"])
    series = session.get(StorySeries, episode.series_id)
    assert series is not None
    label = next(c["label"] for c in episode.choices if c["id"] == choice)
    series.memory = [{**m, "choice": label} if m["number"] == episode.number else m for m in series.memory]
    series.updated_at = utcnow()
    ensure_buffer(session, learner)
    return episode_view(episode)


def rate(session: Session, learner: Learner, episode: StoryEpisode, rating: int) -> dict:
    episode.rating = rating
    return episode_view(episode)


def retry_failed(session: Session, learner: Learner, episode: StoryEpisode) -> dict:
    if episode.status != "failed":
        raise StoryError("only a failed episode can be retried", 409)
    if episode.error_code == "paid_not_approved":
        raise StoryError("paid usage is not approved for this environment", 409)
    episode.status, episode.error_code = "queued", ""
    episode.updated_at = utcnow()
    jobs.enqueue(session, "story_episode", {"episode_id": str(episode.id)},
                 idempotency_key=f"story-episode:{episode.id.hex}:retry:{episode.attempts}", max_attempts=2)
    return episode_view(episode, full=False)


def translate_paragraph(session: Session, settings: Settings, providers: Providers, learner: Learner,
                        episode: StoryEpisode, *, paragraph_index: int, request_id: str) -> dict:
    if episode.status != "ready":
        raise StoryError("this episode is not ready yet", 409)
    if paragraph_index >= len(episode.paragraphs):
        raise StoryError("paragraph not found", 404)
    paragraphs = deepcopy(episode.paragraphs)
    if paragraphs[paragraph_index].get("fa"):
        return {"paragraph_index": paragraph_index, "fa": paragraphs[paragraph_index]["fa"], "cached": True}
    if settings.chat_provider == "azure" and not settings.paid_usage_enabled:
        raise StoryError("paid usage is not approved for this environment", 409)
    messages = translate_messages(paragraphs[paragraph_index]["nl"], "fa")
    estimate = (sum(len(m.content) for m in messages) + len(schema_instruction(Translation))) // 2 + TRANSLATE_MAX_OUTPUT_TOKENS
    call_id = f"story-translate-{episode.id.hex}-{paragraph_index}-{hashlib.sha256(request_id.encode()).hexdigest()[:12]}"
    calls = usage.reserve(session, settings, learner.id, "model_calls", 1, call_id)
    tokens_reservation = usage.reserve(session, settings, learner.id, "tokens", estimate, call_id)
    try:
        result = providers.chat.complete_once(messages, schema=Translation, max_output_tokens=TRANSLATE_MAX_OUTPUT_TOKENS,
                                              temperature=0.0, prompt_version=TRANSLATE_VERSION, request_id=call_id)
    except ProviderError:
        usage.commit(session, calls.id, 1)
        usage.commit(session, tokens_reservation.id, estimate)
        raise
    usage.commit(session, calls.id, 1)
    usage.commit(session, tokens_reservation.id, result.total_tokens)
    if not isinstance(result.parsed, Translation):
        raise ProviderError("unusable translation")
    paragraphs[paragraph_index]["fa"] = result.parsed.translation
    episode.paragraphs = paragraphs
    return {"paragraph_index": paragraph_index, "fa": result.parsed.translation, "cached": False}


def read_aloud_result(episode: StoryEpisode, *, paragraph_index: int, transcript: str) -> dict:
    if paragraph_index >= len(episode.paragraphs):
        raise StoryError("paragraph not found", 404)
    target = tokens(episode.paragraphs[paragraph_index]["nl"])
    heard = tokens(transcript)
    remaining = list(heard)
    matched = 0
    missed: list[str] = []
    for word in target:
        if word in remaining:
            remaining.remove(word)
            matched += 1
        else:
            missed.append(word)
    return {"paragraph_index": paragraph_index, "transcript": transcript, "target_words": len(target),
            "matched_words": matched, "missed": missed[:40], "extra": remaining[:40]}


def record_read_aloud(session: Session, learner: Learner, episode: StoryEpisode, result: dict) -> dict:
    state = dict(episode.answers or {})
    aloud = dict(state.get("read_aloud", {}))
    key = str(result["paragraph_index"])
    previous = aloud.get(key, {})
    share = result["matched_words"] / max(result["target_words"], 1)
    points = 0
    if not previous and share >= 0.5:
        points = POINTS["read_aloud"]
        today.add_points(session, learner.id, points=points, read_aloud=1)
    aloud[key] = {"matched_words": max(result["matched_words"], previous.get("matched_words", 0)),
                  "target_words": result["target_words"], "attempts": previous.get("attempts", 0) + 1}
    state["read_aloud"] = aloud
    episode.answers = state
    return {**result, "points": points}


def export(session: Session, learner_id: uuid.UUID) -> dict:
    series = session.scalar(select(StorySeries).where(StorySeries.learner_id == learner_id))
    if series is None:
        return {"series": None, "episodes": []}
    rows = session.scalars(select(StoryEpisode).where(StoryEpisode.series_id == series.id).order_by(StoryEpisode.number))
    return {"series": series_view(series), "episodes": [episode_view(row) for row in rows]}
