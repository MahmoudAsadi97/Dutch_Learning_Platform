"""Azure AI Speech adapters over the REST endpoints for short audio (at most 60 seconds).

Status: `integration_pending` — written and unit-tested against recorded response shapes
(`tests/fixtures/azure/`), never yet called with credentials. Phase B runs `scripts/verify_live.py`
against a real resource and only then may they be called `verified_live`.

Authentication: a subscription key (`AZURE_SPEECH_KEY`) for the first live run, or an Entra ID token
from a callable (managed identity in Azure) in the documented `aad#<resource id>#<token>` form when
`AZURE_SPEECH_RESOURCE_ID` is set.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import httpx

from dlp.providers.base import (
    AudioResult,
    ProviderError,
    ProviderUnavailable,
    SpeechToText,
    TextToSpeech,
    Transcript,
    TranscriptSegment,
)

TICKS_PER_SECOND = 10_000_000  # the REST API reports offsets and durations in 100-nanosecond ticks
USER_AGENT = "dutch-learning-platform/0.1"


def _auth_headers(key: str, token_provider: Callable[[], str] | None, resource_id: str) -> dict[str, str]:
    if key:
        return {"Ocp-Apim-Subscription-Key": key}
    if token_provider is not None:
        token = token_provider()
        if resource_id:
            return {"Authorization": f"Bearer aad#{resource_id}#{token}"}
        return {"Authorization": f"Bearer {token}"}
    raise ProviderUnavailable("Azure Speech: no key and no token provider configured")


class AzureSpeechToText(SpeechToText):
    name = "azure-speech"

    def __init__(self, key: str, region: str, locale: str = "nl-BE", *, endpoint: str = "",
                 token_provider: Callable[[], str] | None = None, resource_id: str = "",
                 transport: httpx.BaseTransport | None = None, timeout_seconds: float = 60.0) -> None:
        self.key = key
        self.region = region
        self.locale = locale
        self.model = f"azure-stt-{locale}"
        self.endpoint = endpoint or (f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/"
                                     "cognitiveservices/v1")
        self.token_provider = token_provider
        self.resource_id = resource_id
        self._client = httpx.Client(timeout=timeout_seconds, transport=transport)

    def available(self) -> tuple[bool, str]:
        if not self.region:
            return False, "AZURE_SPEECH_REGION not set"
        if not (self.key or self.token_provider):
            return False, "AZURE_SPEECH_KEY not set and no managed identity token provider (integration_pending)"
        return True, f"REST short-audio recognition, {self.locale} in {self.region} (integration_pending until verified live)"

    def transcribe(self, wav_path: Path, *, language: str = "nl", request_id: str = "") -> Transcript:
        started = time.monotonic()
        headers = {
            **_auth_headers(self.key, self.token_provider, self.resource_id),
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-ClientTraceId": request_id or "",
        }
        params = {"language": self.locale, "format": "detailed", "profanity": "raw"}
        try:
            response = self._client.post(self.endpoint, params=params, headers=headers, content=wav_path.read_bytes())
        except httpx.ConnectError as exc:
            raise ProviderUnavailable(f"Azure Speech endpoint unreachable: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Azure Speech request failed: {exc.__class__.__name__}") from exc
        if response.status_code in (401, 403):
            raise ProviderUnavailable(f"Azure Speech refused the credentials (HTTP {response.status_code})")
        if response.status_code >= 400:
            raise ProviderError(f"Azure Speech returned HTTP {response.status_code}")
        data = response.json()
        return parse_recognition(data, language=language, provider=self.name, model=self.model,
                                 latency_ms=int((time.monotonic() - started) * 1000))


def parse_recognition(data: dict[str, Any], *, language: str, provider: str, model: str, latency_ms: int) -> Transcript:
    """Turn the detailed-format reply into a Transcript; an empty result is a valid, empty transcript."""
    status = str(data.get("RecognitionStatus", ""))
    if status == "Error":
        raise ProviderError("Azure Speech returned a recognition error")
    duration = float(data.get("Duration", 0)) / TICKS_PER_SECOND
    offset = float(data.get("Offset", 0)) / TICKS_PER_SECOND
    if status != "Success":
        # NoMatch, InitialSilenceTimeout, BabbleTimeout: nothing recognised, which the caller reports as empty
        return Transcript(text="", language=language, duration_seconds=duration, provider=provider, model=model,
                          segments=[], confidence=None, latency_ms=latency_ms)
    best = (data.get("NBest") or [{}])[0]
    text = str(best.get("Display") or data.get("DisplayText") or "").strip()
    confidence = best.get("Confidence")
    return Transcript(
        text=text, language=language, duration_seconds=duration, provider=provider, model=model,
        segments=[TranscriptSegment(start=offset, end=offset + duration, text=text)] if text else [],
        confidence=float(confidence) if confidence is not None else None, latency_ms=latency_ms,
    )


class AzureTextToSpeech(TextToSpeech):
    name = "azure-speech"
    label = "azure-neural"
    OUTPUT_FORMAT = "riff-16khz-16bit-mono-pcm"

    def __init__(self, key: str, region: str, voice: str = "nl-BE-DenaNeural", *, endpoint: str = "",
                 token_provider: Callable[[], str] | None = None, resource_id: str = "",
                 transport: httpx.BaseTransport | None = None, timeout_seconds: float = 30.0) -> None:
        self.key = key
        self.region = region
        self.voice = voice
        self.endpoint = endpoint or f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.token_provider = token_provider
        self.resource_id = resource_id
        self._client = httpx.Client(timeout=timeout_seconds, transport=transport)

    def available(self) -> tuple[bool, str]:
        if not self.region:
            return False, "AZURE_SPEECH_REGION not set"
        if not (self.key or self.token_provider):
            return False, "AZURE_SPEECH_KEY not set and no managed identity token provider (integration_pending)"
        return True, f"REST synthesis, voice {self.voice} in {self.region} (integration_pending until verified live)"

    def ssml(self, text: str) -> str:
        lang = "-".join(self.voice.split("-")[:2]) or "nl-BE"
        return (f"<speak version='1.0' xml:lang='{lang}'>"
                f"<voice name='{escape(self.voice)}'>{escape(text)}</voice></speak>")

    def synthesize(self, text: str, *, request_id: str = "") -> AudioResult:
        started = time.monotonic()
        headers = {
            **_auth_headers(self.key, self.token_provider, self.resource_id),
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": self.OUTPUT_FORMAT,
            "User-Agent": USER_AGENT,
            "X-ClientTraceId": request_id or "",
        }
        try:
            response = self._client.post(self.endpoint, headers=headers, content=self.ssml(text).encode("utf-8"))
        except httpx.ConnectError as exc:
            raise ProviderUnavailable(f"Azure Speech endpoint unreachable: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Azure Speech request failed: {exc.__class__.__name__}") from exc
        if response.status_code in (401, 403):
            raise ProviderUnavailable(f"Azure Speech refused the credentials (HTTP {response.status_code})")
        if response.status_code >= 400:
            raise ProviderError(f"Azure Speech returned HTTP {response.status_code}")
        wav_bytes = response.content
        if not wav_bytes.startswith(b"RIFF"):
            raise ProviderError("Azure Speech synthesis did not return RIFF/WAV audio")
        return AudioResult(wav_bytes=wav_bytes, sample_rate=16000, voice=self.voice, provider=self.name,
                           label=self.label, latency_ms=int((time.monotonic() - started) * 1000))


def managed_identity_token_provider(scope: str = "https://cognitiveservices.azure.com/.default") -> Callable[[], str]:
    """A token provider backed by DefaultAzureCredential (managed identity in Azure, developer login locally)."""
    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:  # pragma: no cover - depends on the optional extra
        raise ProviderUnavailable("azure-identity is not installed") from exc
    credential = DefaultAzureCredential()

    def provide() -> str:
        return str(credential.get_token(scope).token)

    return provide
