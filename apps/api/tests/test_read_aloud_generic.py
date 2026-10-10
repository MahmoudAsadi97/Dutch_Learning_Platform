"""Reading any text aloud: recognised words only, nothing stored, scored or awarded."""
from __future__ import annotations

from dataclasses import replace

import pytest

from dlp.api.deps import providers_dep
from dlp.domains.speech.compare import read_aloud_compare
from dlp.providers.base import ProviderUnavailable
from dlp.providers.fixtures import FixtureSpeechToText, tone_wav
from dlp.providers.registry import get_providers
from tests.conftest import auth_headers

TEXT = "Goeiedag, ik wil graag een afspraak maken bij de tandarts."


def _post(client, request_id: str, text: str = TEXT, seconds: float = 1.0):
    return client.post("/speech/read-aloud", headers=auth_headers(request_id), data={"text": text},
                       files={"audio": ("take.wav", tone_wav(seconds), "audio/wav")})


def _with_stt(stt):
    from dlp.main import app

    app.dependency_overrides[providers_dep] = lambda: replace(get_providers(), stt=stt)
    return app


def test_words_are_compared_and_nothing_is_kept_scored_or_awarded(client, monkeypatch):
    monkeypatch.setattr(get_providers().blob, "put", lambda *a, **kw: pytest.fail("unexpected recording storage"))
    app = _with_stt(FixtureSpeechToText(default_text="Goeiedag ik wil een afspraak maken bij tandarts"))
    try:
        response = _post(client, "read-aloud-0001")
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"transcript", "target_words", "matched_words", "missed", "extra"}
    assert (body["target_words"], body["matched_words"]) == (10, 8)
    assert body["missed"] == ["graag", "de"] and body["extra"] == []
    usage = client.get("/usage", headers=auth_headers("read-aloud-usage")).json()["counters"]["audio_seconds"]
    assert usage["daily"]["used"] == pytest.approx(1.0), "the audio counts against the allowance"
    today = client.get("/today", headers=auth_headers("read-aloud-today")).json()
    assert today["goal"]["points"] == 0, "practising aloud here earns no points"


def test_the_text_is_bounded(client):
    assert _post(client, "read-aloud-0002", text="").status_code == 422
    assert _post(client, "read-aloud-0003", text="woord " * 120).status_code == 422


@pytest.mark.parametrize("text", [" ", "...", "12 34"])
def test_a_text_without_words_is_refused_before_any_audio_is_counted(client, text):
    refused = _post(client, f"read-aloud-none-{len(text)}", text=text)
    assert refused.status_code == 422 and refused.json()["code"] == "nothing_to_read"
    usage = client.get("/usage", headers=auth_headers("read-aloud-usage-none")).json()["counters"]["audio_seconds"]
    assert usage["daily"]["used"] == 0


def test_the_allowance_and_an_unavailable_service_answer_with_codes(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "usage_daily_audio_seconds", 1)
    assert _post(client, "read-aloud-0004").status_code == 200
    refused = _post(client, "read-aloud-0005")
    assert refused.status_code == 429 and refused.json()["code"] == "usage_limit"

    class Away(FixtureSpeechToText):
        def transcribe(self, *args, **kwargs):
            raise ProviderUnavailable("speech service not configured")

    monkeypatch.setattr(settings, "usage_daily_audio_seconds", 120)
    app = _with_stt(Away())
    try:
        away = _post(client, "read-aloud-0006")
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    assert away.status_code == 503 and away.json()["code"] == "provider_unavailable"


def test_the_comparison_counts_each_heard_word_once():
    result = read_aloud_compare("de kat en de hond", "de kat de kat hond")
    assert result == {"target_words": 5, "matched_words": 4, "missed": ["en"], "extra": ["kat"]}
