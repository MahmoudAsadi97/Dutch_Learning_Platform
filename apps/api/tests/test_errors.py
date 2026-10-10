"""Every expected failure reaches the client as one body shape with a stable code; status codes are unchanged."""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from dlp.api.errors import install_handlers
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.exercises.service import ExerciseError
from dlp.domains.practice.service import PracticeError
from dlp.domains.speech.audio import AudioError
from dlp.domains.stories.service import StoryError
from dlp.domains.stories.vocab import VocabError
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.domains.videos.service import VideoError
from dlp.errors import DomainError
from dlp.providers.base import ProviderError, ProviderUnavailable


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (CurriculumError("stage not found", 404), 404, "curriculum"),
        (StoryError("episode not found", 404), 404, "story"),
        (VideoError("not ready", 409), 409, "video"),
        (PracticeError("session not found", 404), 404, "practice"),
        (AudioError("upload larger than 5 bytes", status_code=413), 413, "audio"),
        (VocabError("word not found", 404), 404, "vocabulary"),
        (ExerciseError("exercise item not found", 404), 404, "exercise"),
        (UsageLimitExceeded("model_calls", "daily", 2, 1), 429, "usage_limit"),
        (DomainError("custom", 418, code="teapot", params={"size": "short"}), 418, "teapot"),
    ],
)
def test_domain_errors_carry_status_code_and_detail(error, status, code):
    assert error.status_code == status
    assert error.code == code
    assert error.reason == error.detail == str(error)
    body = error.body("req-1")
    assert body["detail"] == error.detail and body["code"] == code and body["request_id"] == "req-1"


def test_usage_limit_asks_the_request_to_persist_and_names_the_metric():
    error = UsageLimitExceeded("tokens", "total", 500, 20)
    assert error.persist is True
    assert error.body()["metric"] == "tokens" and error.body()["scope"] == "total"


def _app() -> TestClient:
    app = FastAPI()
    install_handlers(app)

    @app.get("/domain")
    def domain():
        raise PracticeError("session is closed", 409)

    @app.get("/unavailable")
    def unavailable():
        raise ProviderUnavailable("not configured")

    @app.get("/failed")
    def failed():
        raise ProviderError("boom")

    @app.get("/http")
    def http():
        raise HTTPException(status_code=404, detail="not found", headers={"X-Extra": "1"})

    return TestClient(app)


def test_handlers_answer_with_one_body_shape():
    client = _app()
    domain = client.get("/domain", headers={"X-Request-Id": "abc"})
    assert domain.status_code == 409
    assert domain.json() == {"detail": "session is closed", "code": "practice", "request_id": "abc"}
    unavailable = client.get("/unavailable")
    assert unavailable.status_code == 503 and unavailable.json()["code"] == "provider_unavailable"
    assert "boom" not in client.get("/failed").text
    assert client.get("/failed").json()["code"] == "provider_failed"
    http = client.get("/http")
    assert http.status_code == 404 and http.json()["detail"] == "not found" and http.headers["x-extra"] == "1"


def test_real_routes_return_the_code(client, headers):
    missing = client.get(f"/stories/episodes/{uuid.uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "story" and missing.json()["request_id"]
    closed = client.get("/library/zz9", headers=headers)
    assert closed.status_code == 404 and closed.json()["code"] == "curriculum"
