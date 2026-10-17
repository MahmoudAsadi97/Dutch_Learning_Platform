"""Paid allowances survive application rollback and never replay uncertain work.

These use the migrated PostgreSQL test database. Controlled providers do not
make Azure requests or establish real invoice amounts.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.curriculum.writing import WritingReply, writing_feedback
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner
from dlp.domains.identity.service import get_or_create_learner
from dlp.domains.usage import service as usage
from dlp.errors import DomainError
from dlp.providers.base import ChatResult, ProviderError


@pytest.fixture
def paid_settings(settings):
    return settings.model_copy(update={"chat_provider": "azure", "paid_usage_enabled": True,
                                       "usage_daily_tokens": 50000})


@pytest.fixture
def paid_learner(database):
    with session_scope() as session:
        learner = get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com", "Owner",
                                                          "fixture", "paid-sign-in"))
        return learner.id


class ControlledWritingProvider:
    name = "controlled"
    def __init__(self, *, fail=False, invalid=False):
        self.calls = 0
        self.fail = fail
        self.invalid = invalid

    def complete_once(self, messages, **kwargs):
        self.calls += 1
        if self.fail:
            raise ProviderError("controlled response timeout")
        reply = WritingReply.model_validate({"corrections": [], "summary": {
            "nl": "Oefen verder.", "en": "Keep practising.", "fa": "تمرین کنید."}})
        return ChatResult("", None if self.invalid else reply, self.name, "controlled", "test", 12, 8, 1, 1)


def invoke(session, settings, learner_id, provider, *, request_id="durable-writing"):
    return writing_feedback(session, settings, SimpleNamespace(chat_strong=provider), learner_id=learner_id,
                            stage_id="a2", text="Ik wil mijn afspraak verzetten.", request_id=request_id)


def counters(settings, learner_id):
    with session_scope() as session:
        return usage.snapshot(session, settings, learner_id)["counters"]


def test_billed_writing_survives_later_application_rollback(paid_settings, paid_learner):
    provider = ControlledWritingProvider()
    with pytest.raises(RuntimeError, match="application write failed"):
        with session_scope() as session:
            invoke(session, paid_settings, paid_learner, provider)
            raise RuntimeError("application write failed")
    snapshot = counters(paid_settings, paid_learner)
    assert provider.calls == 1
    assert snapshot["model_calls"]["daily"]["used"] == 1
    assert snapshot["tokens"]["daily"]["used"] == 20
    assert snapshot["tokens"]["daily"]["reserved"] == 0


def test_repeated_paid_request_after_rollback_is_not_sent_again(paid_settings, paid_learner):
    provider = ControlledWritingProvider()
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            invoke(session, paid_settings, paid_learner, provider)
            raise RuntimeError("response lost")
    with pytest.raises(DomainError) as caught:
        with session_scope() as session:
            invoke(session, paid_settings, paid_learner, provider)
    assert caught.value.code == "paid_request_replayed" and caught.value.status_code == 409
    assert provider.calls == 1
    assert counters(paid_settings, paid_learner)["model_calls"]["daily"]["used"] == 1


@pytest.mark.parametrize("failure", ["timeout", "invalid-schema"])
def test_uncertain_or_unusable_paid_reply_is_never_refunded(paid_settings, paid_learner, failure):
    provider = ControlledWritingProvider(fail=failure == "timeout", invalid=failure == "invalid-schema")
    with pytest.raises(ProviderError):
        with session_scope() as session:
            invoke(session, paid_settings, paid_learner, provider)
    snapshot = counters(paid_settings, paid_learner)
    assert provider.calls == 1
    assert snapshot["model_calls"]["daily"]["used"] == 1
    assert snapshot["tokens"]["daily"]["used"] >= 20
    assert snapshot["tokens"]["daily"]["reserved"] == 0


def test_token_refusal_releases_unstarted_durable_call(paid_settings, paid_learner):
    provider = ControlledWritingProvider()
    limited = paid_settings.model_copy(update={"usage_daily_tokens": 1})
    with pytest.raises(usage.UsageLimitExceeded):
        with session_scope() as session:
            invoke(session, limited, paid_learner, provider)
    snapshot = counters(limited, paid_learner)
    assert provider.calls == 0
    assert snapshot["model_calls"]["daily"]["used"] == 0
    assert snapshot["model_calls"]["daily"]["reserved"] == 0


def test_unapproved_paid_settings_refuse_before_provider(paid_settings, paid_learner):
    provider = ControlledWritingProvider()
    with session_scope() as session:
        with pytest.raises(DomainError) as caught:
            invoke(session, paid_settings.model_copy(update={"paid_usage_enabled": False}), paid_learner, provider)
        assert caught.value.code == "paid_not_approved" and caught.value.status_code == 403
    assert provider.calls == 0


def test_uncommitted_identity_refuses_paid_dispatch(database, paid_settings):
    provider = ControlledWritingProvider()
    with session_scope() as session:
        learner = get_or_create_learner(session, Principal("fixture:new@example.com", "new@example.com", "New",
                                                          "fixture", "uncommitted-sign-in"))
        with pytest.raises(DomainError) as caught:
            invoke(session, paid_settings, learner.id, provider)
        assert caught.value.code == "paid_identity_pending"
    assert provider.calls == 0


def test_parent_identity_lock_fails_before_provider_instead_of_deadlocking(paid_settings, paid_learner):
    provider = ControlledWritingProvider()
    with session_scope() as session:
        session.scalar(select(Learner).where(Learner.id == paid_learner).with_for_update())
        with pytest.raises(DomainError) as caught:
            invoke(session, paid_settings, paid_learner, provider)
        assert caught.value.code == "usage_accounting"
    assert provider.calls == 0


def test_inflight_reservation_survives_crash_without_refund(paid_settings, paid_learner):
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            calls, tokens = usage.reserve_model(session, paid_settings, paid_learner, 500, "inflight-crash")
            usage.started(session, calls.id, tokens.id)
            raise RuntimeError("worker stopped after dispatch")
    snapshot = counters(paid_settings, paid_learner)
    assert snapshot["model_calls"]["daily"]["reserved"] == 1
    assert snapshot["tokens"]["daily"]["reserved"] == 500


def test_replayed_call_cannot_be_refunded_by_a_later_token_refusal(paid_settings, paid_learner):
    # Simulate a previous process that dispatched work but died before recording
    # completion. The new request has no access to its in-memory started marker.
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            calls = usage.reserve(session, paid_settings, paid_learner, "model_calls", 1, "replay-token-refused")
            usage.started(session, calls.id)
            raise RuntimeError("previous process stopped")
    limited = paid_settings.model_copy(update={"usage_daily_tokens": 1})
    with pytest.raises(usage.UsageLimitExceeded):
        with session_scope() as session:
            usage.reserve_model(session, limited, paid_learner, 500, "replay-token-refused")
    snapshot = counters(limited, paid_learner)["model_calls"]["daily"]
    assert snapshot["used"] + snapshot["reserved"] == 1, "uncertain prior work is never made available for free"


def test_repeated_settlement_does_not_double_count(paid_settings, paid_learner):
    from concurrent.futures import ThreadPoolExecutor
    with session_scope() as session:
        reservation = usage.reserve(session, paid_settings, paid_learner, "tokens", 500, "same-settlement")
    def settle():
        with session_scope() as session:
            same = usage.reserve(session, paid_settings, paid_learner, "tokens", 500, "same-settlement")
            assert same.id == reservation.id and same.deduplicated
            usage.commit(session, same.id, 200)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(settle) for _ in range(2)]
        for future in futures:
            future.result(timeout=10)
    snapshot = counters(paid_settings, paid_learner)["tokens"]["daily"]
    assert snapshot["used"] == 200 and snapshot["reserved"] == 0


def test_retired_paid_render_keeps_prior_expenditure_despite_parent_rollback(paid_settings, paid_learner):
    from dlp.domains.videos import service as videos
    from dlp.domains.videos.models import VideoLesson
    azure_narration = paid_settings.model_copy(update={"video_provider": "cards", "tts_provider": "azure",
                                                     "usage_daily_video_seconds": 300, "usage_total_video_seconds": 7200})
    with session_scope() as session:
        reservation = usage.reserve(session, azure_narration, paid_learner, "video_seconds", 40, "retired-paid-render")
        usage.started(session, reservation.id)
        lesson = VideoLesson(learner_id=paid_learner, stage_id="a2", status="rendering", renderer="scene-cards",
                             checks={"video_reservation": str(reservation.id), "estimated_seconds": 40,
                                     "paid_render": True}, scenes=[{"nl": "Ik wacht."}])
        session.add(lesson)
        session.flush()
        lesson_id = lesson.id
    with pytest.raises(RuntimeError, match="parent write failed"):
        with session_scope() as session:
            assert videos.retire_pending(session, {"video_id": str(lesson_id)})["generation_enabled"] is False
            raise RuntimeError("parent write failed")
    snapshot = counters(azure_narration, paid_learner)["video_seconds"]["daily"]
    assert snapshot["used"] == 40 and snapshot["reserved"] == 0
    # The durable settlement is safe when the failed status transaction is retried.
    with session_scope() as session:
        videos.retire_pending(session, {"video_id": str(lesson_id)})
    assert counters(azure_narration, paid_learner)["video_seconds"]["daily"]["used"] == 40


def test_retired_local_render_releases_only_an_unbilled_reservation(paid_settings, paid_learner):
    from dlp.domains.videos import service as videos
    from dlp.domains.videos.models import VideoLesson
    local = paid_settings.model_copy(update={"video_provider": "cards", "tts_provider": "local",
                                               "usage_daily_video_seconds": 300, "usage_total_video_seconds": 7200})
    with session_scope() as session:
        reservation = usage.reserve(session, local, paid_learner, "video_seconds", 30, "retired-local-render")
        lesson = VideoLesson(learner_id=paid_learner, stage_id="a2", status="rendering", renderer="scene-cards",
                             checks={"video_reservation": str(reservation.id), "estimated_seconds": 30,
                                     "paid_render": False})
        session.add(lesson)
        session.flush()
        assert videos.retire_pending(session, {"video_id": str(lesson.id)}) == {
            "status": "failed", "generation_enabled": False,
        }
    snapshot = counters(local, paid_learner)["video_seconds"]["daily"]
    assert snapshot["used"] == 0 and snapshot["reserved"] == 0


def test_legacy_cards_with_persisted_neural_voice_keep_uncertain_allowance(paid_settings, paid_learner):
    from dlp.domains.videos import service as videos
    from dlp.domains.videos.models import VideoLesson
    azure_narration = paid_settings.model_copy(update={"video_provider": "cards", "tts_provider": "azure",
                                                     "usage_daily_video_seconds": 300, "usage_total_video_seconds": 7200})
    with session_scope() as session:
        reservation = usage.reserve(session, azure_narration, paid_learner, "video_seconds", 30, "legacy-neural-cards")
        lesson = VideoLesson(learner_id=paid_learner, stage_id="a2", status="rendering", renderer="scene-cards",
                             voice="nl-BE-DenaNeural", checks={"video_reservation": str(reservation.id),
                                                            "estimated_seconds": 30})
        session.add(lesson)
        session.flush()
        lesson_id = lesson.id
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            videos._settle_reservation(session, session.get(VideoLesson, lesson_id), None)
            raise RuntimeError("legacy job status write rolled back")
    snapshot = counters(azure_narration, paid_learner)["video_seconds"]["daily"]
    assert snapshot["used"] == 30 and snapshot["reserved"] == 0
