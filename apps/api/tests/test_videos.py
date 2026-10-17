"""Video creation is retired; stale clients and queued work cannot incur new provider charges.

Existing owner-scoped records and media remain readable without a destructive migration.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from dlp.config import Settings, get_settings
from dlp.db.base import utcnow
from dlp.db.session import session_scope
from dlp.domains.identity.models import Learner
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.service import drain, enqueue
from dlp.domains.usage.models import UsageReservation
from dlp.domains.videos import service
from dlp.domains.videos.models import VideoLesson
from dlp.providers.base import ProviderUnavailable, VideoRequest, VideoScene
from dlp.providers.registry import build_video, get_providers, video_mode

from .conftest import auth_headers


class ForbiddenProvider:
    """Accessing any provider capability fails the test before even a fixture call occurs."""

    def __getattr__(self, name):
        raise AssertionError(f"retired generation accessed provider capability {name}")


@pytest.mark.parametrize("mode", ["disabled", "auto", "avatar", "cards", "fixture"])
@pytest.mark.parametrize("speech", ["azure", "local", "fixture"])
def test_legacy_configuration_always_builds_a_closed_renderer(mode, speech, settings):
    configured = settings.model_copy(update={"video_provider": mode, "tts_provider": speech})
    assert video_mode(configured) == "disabled"
    renderer = build_video(configured, ForbiddenProvider())
    assert renderer.name == "disabled" and renderer.available()[0] is False
    request = VideoRequest(scenes=[VideoScene("Dag.", "dag")], title="Dag")
    with pytest.raises(ProviderUnavailable, match="retired"):
        renderer.start(request)
    with pytest.raises(ProviderUnavailable, match="retired"):
        renderer.status("old-provider-job")
    with pytest.raises(ProviderUnavailable, match="retired"):
        renderer.fetch("old-provider-job", Path("not-written.mp4"))


def test_domain_creation_and_retry_reject_before_database_or_provider_access():
    with pytest.raises(service.VideoError) as create:
        service.request_video(None, None, stage_id="a1", topic="markt", kind="verhaal", request_id="old-client")
    assert create.value.status_code == 410
    with pytest.raises(service.VideoError) as retry:
        service.retry_failed(None, None, None)
    assert retry.value.status_code == 410



@pytest.mark.parametrize("status", ["queued", "writing", "rendering"])
def test_registered_jobs_close_pending_work_without_resolving_any_provider(status, monkeypatch):
    lesson = SimpleNamespace(status=status, checks={}, error_code="", updated_at=None)
    session = SimpleNamespace(scalar=lambda statement: lesson)
    calls = []
    monkeypatch.setattr(service, "_settle_reservation", lambda session, lesson, seconds: calls.append(seconds))
    result = service.video_script_job(session, {"video_id": str(uuid.uuid4())})
    assert result == {"status": "failed", "generation_enabled": False}
    assert lesson.error_code == "retired" and calls == [None]
    # Duplicate render work cannot repeat accounting or dispatch a provider.
    assert service.video_render_job(session, {"video_id": str(uuid.uuid4())}) == result
    assert calls == [None]

def _historical(client, *, status="ready", renderer="azure-avatar", checks=None):
    # Sign in through the real identity boundary before creating historical test data.
    assert client.get("/me", headers=auth_headers()).status_code == 200
    with session_scope() as session:
        learner = session.scalar(select(Learner))
        assert learner is not None
        lesson = VideoLesson(
            learner_id=learner.id, stage_id="a1", status=status, renderer=renderer,
            title="Op de markt", scenes=[{"nl": "Ik koop appels.", "en": "I buy apples.", "fa": "سیب می‌خرم."}],
            checks=checks or {}, media_key="archive/example.mp4", media_bytes=512, ready_at=utcnow(),
            cues=[{"start": 0, "end": 1, "text": "Ik koop appels.", "scene": 0}],
        )
        session.add(lesson)
        session.flush()
        return lesson.id


def test_old_client_creation_and_retry_are_gone_and_create_no_work(client, monkeypatch):
    monkeypatch.setattr(get_providers(), "video", ForbiddenProvider())
    monkeypatch.setattr(get_providers(), "chat", ForbiddenProvider())
    monkeypatch.setattr(get_providers(), "chat_strong", ForbiddenProvider())
    monkeypatch.setattr(get_providers(), "tts", ForbiddenProvider())
    response = client.post("/videos", headers=auth_headers("retired-create-0001"), json={
        "request_id": "retired-create-0001", "stage_id": "a1", "topic": "markt", "kind": "verhaal",
    })
    assert response.status_code == 410 and response.json()["code"] == "video"
    retry = client.post(f"/videos/{uuid.uuid4()}/retry", headers=auth_headers("retired-retry-0001"))
    assert retry.status_code == 410
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(VideoLesson)) == 0
        assert session.scalar(select(func.count()).select_from(Job)) == 0
        assert session.scalar(select(func.count()).select_from(UsageReservation)) == 0


def test_historical_owned_records_media_and_subtitles_are_preserved(client):
    video_id = _historical(client)
    blob = get_providers().blob
    data = bytes(range(256)) * 2
    blob.put("archive/example.mp4", data, content_type="video/mp4")
    listing = client.get("/videos", headers=auth_headers()).json()
    assert listing["generation_enabled"] is False and listing["replacement_url"] == "/verhalen"
    assert listing["max_pending"] == 0 and [item["id"] for item in listing["items"]] == [str(video_id)]
    detail = client.get(f"/videos/{video_id}", headers=auth_headers())
    assert detail.status_code == 200 and detail.json()["title"] == "Op de markt"
    media = client.get(f"/videos/{video_id}/media", headers={**auth_headers(), "Range": "bytes=100-199"})
    assert media.status_code == 206 and media.content == data[100:200]
    assert media.headers["content-range"] == "bytes 100-199/512"
    subtitles = client.get(f"/videos/{video_id}/subtitles.vtt", headers=auth_headers())
    assert subtitles.status_code == 200 and "Ik koop appels." in subtitles.text
    other = client.get(f"/videos/{video_id}", headers=auth_headers(email="second@example.com"))
    assert other.status_code == 404, "retirement does not weaken owner isolation"
    with session_scope() as session:
        saved = session.get(VideoLesson, video_id)
        assert saved is not None and saved.status == "ready" and saved.media_key == "archive/example.mp4"


@pytest.mark.parametrize("kind,status", [("video_script", "queued"), ("video_script", "writing"), ("video_render", "rendering")])
def test_pre_upgrade_jobs_retire_without_any_provider_call(client, monkeypatch, kind, status):
    video_id = _historical(client, status=status)
    providers = get_providers()
    for name in ("video", "chat", "chat_strong", "tts", "blob"):
        monkeypatch.setattr(providers, name, ForbiddenProvider())
    with session_scope() as session:
        enqueue(session, kind, {"video_id": str(video_id)}, idempotency_key=f"retire-{video_id}")
    assert drain(get_settings()) == 1
    with session_scope() as session:
        lesson = session.get(VideoLesson, video_id)
        assert lesson is not None and lesson.status == "failed" and lesson.error_code == "retired"
        assert lesson.scenes and lesson.media_key == "archive/example.mp4", "existing data is retained"
        assert session.scalar(select(func.count()).select_from(UsageReservation)) == 0
        jobs = list(session.scalars(select(Job)))
        assert len(jobs) == 1 and jobs[0].status == "done"
        assert jobs[0].result["generation_enabled"] is False


def test_ready_videos_are_not_recommended_as_an_active_feature(client):
    _historical(client)
    plan = client.get("/today", headers=auth_headers()).json()
    assert plan["videos"] == {"ready": None, "pending": 0}


@pytest.mark.parametrize("action,body", [
    ("watched", None), ("retry", None), ("rating", {"rating": 1}),
    ("answers", {"request_id": "retired-answer-0001", "answers": {"0": 0}}), ("words", {"term": "de markt"}),
])
def test_legacy_mutations_are_retired_without_modifying_historical_data(client, action, body):
    video_id = _historical(client)
    response = client.post(f"/videos/{video_id}/{action}", headers=auth_headers("retired-action-0001"), json=body)
    assert response.status_code == 410 and response.json()["replacement_url"] == "/verhalen"
    with session_scope() as session:
        lesson = session.get(VideoLesson, video_id)
        assert lesson is not None and lesson.status == "ready" and lesson.watched_at is None and lesson.rating == 0


def test_retired_video_defaults_have_no_new_allowance():
    assert Settings.model_fields["usage_daily_video_seconds"].default == 0
    assert Settings.model_fields["usage_total_video_seconds"].default == 0
    assert Settings.model_fields["video_provider"].default == "disabled"
