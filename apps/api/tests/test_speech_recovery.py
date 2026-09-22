"""Real database and ffmpeg; deterministic providers with injected cloud failures."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from dlp.providers.base import ProviderError
from dlp.providers.fixtures import FixtureSpeechToText, tone_wav
from dlp.providers.registry import get_providers
from tests.conftest import auth_headers
from tests.test_turns import _say, _start


def upload(client, request_id="recovery-speech-001", path="/speech/transcribe", **data):
    return client.post(path, headers=auth_headers(request_id),
                       files={"audio": ("turn.wav", tone_wav(1), "audio/wav")}, data=data)


def counters(client):
    return client.get("/usage", headers=auth_headers("recovery-usage-001")).json()["counters"]


def storage_failure(*args, **kwargs):
    raise ProviderError("injected storage outage")


def test_repeated_transcription_id_counts_each_call_without_overwriting_audio(client):
    first = upload(client)
    second = upload(client)
    assert first.status_code == second.status_code == 200
    assert first.json()["audio"]["blob_key"] != second.json()["audio"]["blob_key"]
    assert first.json()["audio"]["asset_id"] != second.json()["audio"]["asset_id"]
    assert counters(client)["audio_seconds"]["daily"]["used"] == 2


def test_repeated_synthesis_id_counts_each_call_and_cannot_bypass_limit(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "usage_daily_audio_seconds", 2)
    for _ in range(2):
        response = client.post("/speech/synthesize", headers=auth_headers("recovery-tts-001"), json={"text": "Dag."})
        assert response.status_code == 200
    refused = client.post("/speech/synthesize", headers=auth_headers("recovery-tts-001"), json={"text": "Dag."})
    assert refused.status_code == 429
    assert counters(client)["audio_seconds"]["daily"]["used"] == pytest.approx(1.2)


def test_same_trace_id_in_different_sessions_charges_each_real_turn(client):
    request_id = "r" * 64  # the full supported length must also work for the synthesized reply
    first_id = _start(client)
    first = _say(client, first_id, request_id, "Ik moet werken.")
    assert first.status_code == 200, first.text
    assert first.json()["turn"]["character_audio_asset_id"]
    assert client.post(f"/practice/sessions/{first_id}/abandon", headers=auth_headers("close-old-session")).status_code == 200
    second_id = _start(client, "new-session-0001")
    second = _say(client, second_id, request_id, "Ik moet werken.")
    assert second.status_code == 200, second.text
    assert second.json()["turn"]["character_audio_asset_id"] != first.json()["turn"]["character_audio_asset_id"]
    assert counters(client)["model_calls"]["daily"]["used"] == 4


def test_storage_outage_keeps_transcript_and_usage(client, monkeypatch):
    monkeypatch.setattr(get_providers().blob, "put", storage_failure)
    response = upload(client)
    assert response.status_code == 200
    assert response.json()["transcript"]["text"]
    assert response.json()["audio"]["stored"] is False
    assert response.json()["audio"]["blob_key"] is None
    assert response.json()["audio"]["storage_warning"] == "recording_not_saved"
    assert counters(client)["audio_seconds"]["daily"]["used"] == 1


def test_storage_outage_still_returns_generated_playback(client, monkeypatch):
    monkeypatch.setattr(get_providers().blob, "put", storage_failure)
    response = client.post("/speech/synthesize", headers=auth_headers("storage-tts-001"),
                           json={"text": "Dag.", "store": True})
    assert response.status_code == 200 and response.content.startswith(b"RIFF")
    assert response.headers["x-audio-storage-warning"] == "audio_not_saved"
    assert "x-audio-asset-id" not in response.headers
    assert counters(client)["audio_seconds"]["daily"]["used"] == pytest.approx(0.6)


def test_microphone_check_does_not_write_a_blob(client, monkeypatch):
    monkeypatch.setattr(get_providers().blob, "put", lambda *a, **kw: pytest.fail("unexpected recording storage"))
    response = upload(client, keep_recording="false")
    assert response.status_code == 200
    assert response.json()["audio"]["stored"] is False
    assert response.json()["audio"]["storage_warning"] is None


def listening_url(client):
    mission = client.get("/missions/appointment-change", headers=auth_headers()).json()
    step = next(s for s in mission["document"]["steps"] if s["payload"]["type"] == "listening")
    return "/missions/appointment-change/audio/" + step["payload"]["audio_key"]


def test_listening_survives_cache_outage_and_counts_usage(client, monkeypatch):
    url = listening_url(client)
    blob = get_providers().blob
    monkeypatch.setattr(blob, "exists", storage_failure)
    monkeypatch.setattr(blob, "put", storage_failure)
    response = client.get(url, headers=auth_headers("listening-down-001"))
    assert response.status_code == 200 and response.content.startswith(b"RIFF")
    assert response.headers["x-audio-storage-warning"] == "audio_not_cached"
    assert counters(client)["audio_seconds"]["daily"]["used"] > 0


def test_changing_voice_or_content_invalidates_listening_cache(client, monkeypatch):
    url = listening_url(client)
    first = client.get(url, headers=auth_headers("listening-cache-001"))
    assert first.status_code == 200
    first_usage = counters(client)["audio_seconds"]["daily"]["used"]
    monkeypatch.setattr(get_providers().tts, "voice", "a-new-test-voice")
    second = client.get(url, headers=auth_headers("listening-cache-002"))
    assert second.headers["x-audio-voice"] == "a-new-test-voice"
    assert counters(client)["audio_seconds"]["daily"]["used"] > first_usage
    second_usage = counters(client)["audio_seconds"]["daily"]["used"]
    # Mutate only the test database's content version; a reloaded lesson must not serve stale audio.
    from dlp.db.session import session_scope
    from dlp.domains.content.models import Mission

    with session_scope() as db:
        record = db.get(Mission, "appointment-change")
        original_hash = record.content_hash
        record.content_hash = "changed-test-version"
    try:
        third = client.get(url, headers=auth_headers("listening-cache-003"))
        assert third.status_code == 200
        assert counters(client)["audio_seconds"]["daily"]["used"] > second_usage
    finally:
        with session_scope() as db:
            db.get(Mission, "appointment-change").content_hash = original_hash


def test_spoken_turn_survives_storage_outage(client, monkeypatch):
    session_id = _start(client)
    monkeypatch.setattr(get_providers().blob, "put", storage_failure)
    response = upload(client, path=f"/practice/sessions/{session_id}/turns/speech", step_key="speak-call")
    assert response.status_code == 200, response.text
    turn = response.json()["turn"]
    assert turn["status"] == "completed" and turn["learner_text"] and turn["character_text"]
    assert turn["recording_warning"] == "recording_not_saved"
    assert turn["character_audio_asset_id"] is None and turn["audio_error"]
    before = counters(client)
    again = upload(client, path=f"/practice/sessions/{session_id}/turns/speech", step_key="speak-call")
    assert again.json()["deduplicated"] is True
    assert counters(client) == before, "a persisted turn retry must make no paid calls"


@pytest.mark.parametrize("failure", ["empty", "too_long", "model_limit", "token_limit"])
def test_transcription_usage_survives_a_later_turn_refusal(client, settings, monkeypatch, failure):
    session_id = _start(client)
    providers = get_providers()
    original = providers.stt.transcribe

    def transcribe(*args, **kwargs):
        result = original(*args, **kwargs)
        if failure == "empty":
            result.text = ""
        if failure == "too_long":
            result.text = "x" * 601
        return result

    monkeypatch.setattr(providers.stt, "transcribe", transcribe)
    if failure == "model_limit":
        monkeypatch.setattr(settings, "usage_daily_model_calls", 1)
    if failure == "token_limit":
        monkeypatch.setattr(settings, "usage_daily_tokens", 1)
    response = upload(client, path=f"/practice/sessions/{session_id}/turns/speech", step_key="speak-call")
    assert response.status_code == {"empty": 422, "too_long": 413}.get(failure, 429), response.text
    current = counters(client)
    assert current["audio_seconds"]["daily"]["used"] == 1
    assert current["audio_seconds"]["daily"]["reserved"] == 0
    for metric in ("model_calls", "tokens"):
        assert current[metric]["daily"]["used"] == current[metric]["daily"]["reserved"] == 0


@pytest.mark.parametrize("practice", [False, True])
def test_slow_transcription_does_not_block_health_requests(client, monkeypatch, practice):
    path = f"/practice/sessions/{_start(client)}/turns/speech" if practice else "/speech/transcribe"
    started, release = threading.Event(), threading.Event()
    original = FixtureSpeechToText().transcribe

    def slow(*args, **kwargs):
        started.set()
        assert release.wait(5), "test did not release the blocked provider"
        return original(*args, **kwargs)

    monkeypatch.setattr(get_providers().stt, "transcribe", slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(upload, client, path=path, step_key="speak-call")
        try:
            assert started.wait(5)
            health = pool.submit(client.get, "/health")
            assert health.result(timeout=2).status_code == 200
        finally:
            release.set()
        assert pending.result(timeout=10).status_code == 200
