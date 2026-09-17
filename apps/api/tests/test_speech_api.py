import io
import shutil
import wave

import pytest

from dlp.providers.fixtures import FixtureSpeechToText, tone_wav
from dlp.providers.registry import get_providers
from tests.conftest import FIXTURES, auth_headers
from tests.test_audio import make_webm_opus

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@needs_ffmpeg
def test_transcribe_webm_upload_end_to_end(client, tmp_path):
    source = tmp_path / "rec.webm"
    make_webm_opus(source, seconds=1.2)
    response = client.post(
        "/speech/transcribe", headers=auth_headers("speech-req-0001"),
        files={"audio": ("rec.webm", source.read_bytes(), "audio/webm")}, data={"keep_recording": "true"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["request_id"] == "speech-req-0001"
    assert body["transcript"]["provider"] == "fixture"
    assert body["transcript"]["text"] == "Ik wil mijn afspraak verzetten."
    assert body["audio"]["source"]["codec"] == "opus"
    assert body["audio"]["canonical"] == {**body["audio"]["canonical"], "codec": "pcm_s16le", "sample_rate": 16000, "channels": 1}
    assert body["evidence"] == {"modality": "speech", "kind": "transcript"}

    providers = get_providers()
    assert providers.blob.exists(body["audio"]["blob_key"])
    stored = providers.blob.get(body["audio"]["blob_key"])
    with wave.open(io.BytesIO(stored), "rb") as handle:
        assert handle.getframerate() == 16000 and handle.getnchannels() == 1

    usage = client.get("/usage", headers=auth_headers("speech-req-0002")).json()["counters"]["audio_seconds"]
    assert 1.0 <= usage["daily"]["used"] <= 1.5
    assert usage["daily"]["reserved"] == 0


@needs_ffmpeg
def test_sidecar_transcript_is_used_for_recorded_fixture(client):
    wav = (FIXTURES / "tone_1s.wav").read_bytes()
    response = client.post("/speech/transcribe", headers=auth_headers("speech-req-0003"),
                           files={"audio": ("tone_1s.wav", wav, "audio/wav")})
    assert response.status_code == 200
    assert response.json()["transcript"]["text"]


def test_oversized_upload_is_refused(client, settings):
    payload = b"0" * (settings.max_upload_bytes + 1)
    response = client.post("/speech/transcribe", headers=auth_headers("speech-req-0004"),
                           files={"audio": ("big.webm", payload, "audio/webm")})
    assert response.status_code == 413


@needs_ffmpeg
def test_provider_failure_releases_the_reservation(client, monkeypatch):
    providers = get_providers()
    monkeypatch.setattr(providers, "stt", FixtureSpeechToText(fail_first=1))
    response = client.post("/speech/transcribe", headers=auth_headers("speech-req-0005"),
                           files={"audio": ("tone.wav", tone_wav(1.0), "audio/wav")})
    assert response.status_code == 502
    usage = client.get("/usage", headers=auth_headers("speech-req-0006")).json()["counters"]["audio_seconds"]
    assert usage["daily"]["reserved"] == 0 and usage["daily"]["used"] == 0


@needs_ffmpeg
def test_daily_audio_limit_returns_429(client, settings):
    # the test configuration allows 120 seconds per day and 12 seconds per recording
    for index in range(10):
        response = client.post("/speech/transcribe", headers=auth_headers(f"speech-limit-{index:04d}"),
                               files={"audio": ("tone.wav", tone_wav(12.0), "audio/wav")})
        assert response.status_code == 200, response.text
    response = client.post("/speech/transcribe", headers=auth_headers("speech-limit-over"),
                           files={"audio": ("tone.wav", tone_wav(5.0), "audio/wav")})
    assert response.status_code == 429


def test_synthesize_returns_labelled_wav(client):
    response = client.post("/speech/synthesize", headers=auth_headers("tts-req-0001"),
                           json={"text": "Goeiedag, u spreekt met Tandartspraktijk Molenstraat."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["x-audio-label"] == "synthetic-development"
    with wave.open(io.BytesIO(response.content), "rb") as handle:
        assert handle.getnchannels() == 1 and handle.getnframes() > 1000
    usage = client.get("/usage", headers=auth_headers("tts-req-0002")).json()["counters"]["audio_seconds"]
    assert usage["daily"]["used"] > 0 and usage["daily"]["reserved"] == 0


def test_synthesize_rejects_empty_and_huge_text(client):
    assert client.post("/speech/synthesize", headers=auth_headers("tts-req-0003"), json={"text": ""}).status_code == 422
    assert client.post("/speech/synthesize", headers=auth_headers("tts-req-0004"),
                       json={"text": "x" * 601}).status_code == 422
