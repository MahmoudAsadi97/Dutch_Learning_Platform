"""Azure Speech adapters against recorded reply shapes; no network, no credentials (integration_pending)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from dlp.providers.base import ProviderError, ProviderUnavailable
from dlp.providers.fixtures import tone_wav
from dlp.providers.speech_azure import AzureSpeechToText, AzureTextToSpeech, parse_recognition

AZURE = Path(__file__).resolve().parent / "fixtures" / "azure"


def _stt(handler, **kwargs) -> AzureSpeechToText:
    return AzureSpeechToText("secret-key", "westeurope", "nl-BE", transport=httpx.MockTransport(handler), **kwargs)


def _tts(handler, **kwargs) -> AzureTextToSpeech:
    return AzureTextToSpeech("secret-key", "westeurope", "nl-BE-DenaNeural", transport=httpx.MockTransport(handler), **kwargs)


def test_recognition_request_shape_and_parsing(tmp_path):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        seen["body"] = request.content
        return httpx.Response(200, json=json.loads((AZURE / "stt_success.json").read_text()))

    wav = tmp_path / "turn.wav"
    wav.write_bytes(tone_wav(1.0))
    transcript = _stt(handler).transcribe(wav, language="nl", request_id="req-azure-0001")
    assert seen["url"].startswith("https://westeurope.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1")
    assert "language=nl-BE" in seen["url"] and "format=detailed" in seen["url"]
    assert seen["headers"]["ocp-apim-subscription-key"] == "secret-key"
    assert seen["headers"]["content-type"] == "audio/wav; codecs=audio/pcm; samplerate=16000"
    assert seen["headers"]["x-clienttraceid"] == "req-azure-0001"
    assert seen["body"] == wav.read_bytes()
    assert transcript.text == "Ik moet werken, dus ik kan woensdag niet komen."
    assert transcript.provider == "azure-speech" and transcript.model == "azure-stt-nl-BE"
    assert transcript.duration_seconds == pytest.approx(2.15)
    assert transcript.confidence == pytest.approx(0.9312)
    assert transcript.segments[0].start == pytest.approx(0.3) and transcript.segments[0].end == pytest.approx(2.45)


def test_no_match_is_an_empty_transcript_not_an_error():
    transcript = parse_recognition(json.loads((AZURE / "stt_nomatch.json").read_text()), language="nl",
                                   provider="azure-speech", model="m", latency_ms=1)
    assert transcript.text == "" and transcript.segments == [] and transcript.duration_seconds == pytest.approx(1.2)
    with pytest.raises(ProviderError):
        parse_recognition({"RecognitionStatus": "Error"}, language="nl", provider="p", model="m", latency_ms=1)


def test_refused_credentials_are_reported_as_unavailable(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Access denied")

    wav = tmp_path / "turn.wav"
    wav.write_bytes(tone_wav(0.5))
    with pytest.raises(ProviderUnavailable, match="refused the credentials"):
        _stt(handler).transcribe(wav)


def test_managed_identity_token_header_shape(tmp_path):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=json.loads((AZURE / "stt_success.json").read_text()))

    wav = tmp_path / "turn.wav"
    wav.write_bytes(tone_wav(0.5))
    stt = AzureSpeechToText("", "westeurope", token_provider=lambda: "tok-123",
                            resource_id="/subscriptions/x/resourceGroups/y/providers/Microsoft.CognitiveServices/accounts/z",
                            transport=httpx.MockTransport(handler))
    stt.transcribe(wav)
    assert seen["auth"] == "Bearer aad#/subscriptions/x/resourceGroups/y/providers/Microsoft.CognitiveServices/accounts/z#tok-123"
    assert AzureSpeechToText("", "westeurope").available() == (
        False, "AZURE_SPEECH_KEY not set and no managed identity token provider (integration_pending)")


def test_synthesis_request_shape_and_wav_result():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(200, content=tone_wav(0.8), headers={"Content-Type": "audio/wav"})

    result = _tts(handler).synthesize("Goeiedag, Tandartspraktijk Molenstraat, met Els.", request_id="req-azure-0002")
    assert seen["url"] == "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
    assert seen["headers"]["x-microsoft-outputformat"] == "riff-16khz-16bit-mono-pcm"
    assert seen["headers"]["content-type"] == "application/ssml+xml"
    assert seen["body"] == ("<speak version='1.0' xml:lang='nl-BE'><voice name='nl-BE-DenaNeural'>"
                            "Goeiedag, Tandartspraktijk Molenstraat, met Els.</voice></speak>")
    assert result.wav_bytes.startswith(b"RIFF") and result.sample_rate == 16000
    assert result.label == "azure-neural" and result.voice == "nl-BE-DenaNeural"


def test_synthesis_escapes_markup_and_rejects_non_wav():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "&lt;b&gt;" in request.content.decode("utf-8")
        return httpx.Response(200, content=b"not audio")

    with pytest.raises(ProviderError, match="RIFF"):
        _tts(handler).synthesize("<b>hallo</b>")
