"""Azure AI Speech text-to-speech avatar, through the batch synthesis REST API (2024-08-01).

One request renders the whole script as a single MP4 (H.264, AAC) with the subtitles soft-embedded as a
text track, which the service times itself. The job is asynchronous: `start` submits it, `status` is polled
by the video job, `fetch` downloads the result from the signed URL the service hands back, and `cleanup`
deletes the job so nothing lingers on the service side beyond its time to live.

Authentication: a subscription key, or an Entra ID token (managed identity in Azure) against the resource's
custom domain, which this API requires for token authentication. Batch avatar synthesis is available in
West Europe; the standard avatar is billed per second of video, on top of the characters synthesised.
"""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import httpx

from dlp.providers.base import ProviderError, ProviderUnavailable, VideoJobStatus, VideoRenderer, VideoRequest

API_VERSION = "2024-08-01"
USER_AGENT = "dutch-learning-platform/0.1"
SCENE_PAUSE_MS = 700


def endpoint_for(*, endpoint: str = "", resource_id: str = "", region: str = "") -> str:
    """The resource's custom domain when it can be known, else the regional endpoint (key authentication only)."""
    if endpoint:
        return endpoint.rstrip("/")
    account = resource_id.rstrip("/").rsplit("/", 1)[-1] if resource_id else ""
    if account:
        return f"https://{account}.cognitiveservices.azure.com"
    if region:
        return f"https://{region}.api.cognitive.microsoft.com"
    return ""


def script_ssml(request: VideoRequest, voice: str) -> str:
    """One `<voice>` with a short pause between scenes; everything the presenter says is escaped text."""
    lang = request.language or "-".join(voice.split("-")[:2]) or "nl-BE"
    parts = [escape(scene.text) for scene in request.scenes if scene.text.strip()]
    body = f'<break time="{SCENE_PAUSE_MS}ms"/>'.join(parts)
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
            f'<voice name="{escape(voice)}"><break time="400ms"/>{body}<break time="600ms"/></voice></speak>')


class AzureAvatarRenderer(VideoRenderer):
    name = "azure-avatar"
    label = "avatar"

    def __init__(self, *, key: str = "", endpoint: str, voice: str, character: str = "lisa",
                 style: str = "graceful-sitting", background: str = "#F4EFE6FF", bitrate_kbps: int = 1800,
                 token_provider: Callable[[], str] | None = None, transport: httpx.BaseTransport | None = None,
                 timeout_seconds: float = 30.0, time_to_live_hours: int = 24) -> None:
        self.key = key
        self.endpoint = endpoint.rstrip("/")
        self.voice = voice
        self.character = character
        self.style = style
        self.background = background
        self.bitrate_kbps = bitrate_kbps
        self.token_provider = token_provider
        self.time_to_live_hours = time_to_live_hours
        self._client = httpx.Client(timeout=timeout_seconds, transport=transport, follow_redirects=True)

    # --- plumbing ---------------------------------------------------------------------------------------

    def available(self) -> tuple[bool, str]:
        if not self.endpoint:
            return False, "no Speech endpoint: set AZURE_SPEECH_ENDPOINT, a resource id or a region"
        if not (self.key or self.token_provider):
            return False, "AZURE_SPEECH_KEY not set and no managed identity token provider"
        return True, f"batch avatar {self.character}/{self.style}, voice {self.voice}, at {self.endpoint}"

    def _headers(self) -> dict[str, str]:
        if self.key:
            auth = {"Ocp-Apim-Subscription-Key": self.key}
        elif self.token_provider is not None:
            auth = {"Authorization": f"Bearer {self.token_provider()}"}
        else:
            raise ProviderUnavailable("Azure avatar: no key and no token provider configured")
        return {**auth, "User-Agent": USER_AGENT, "Accept": "application/json"}

    def _url(self, job_id: str) -> str:
        return f"{self.endpoint}/avatar/batchsyntheses/{job_id}?api-version={API_VERSION}"

    def _call(self, method: str, url: str, *, json: dict[str, Any] | None = None) -> httpx.Response:
        try:
            response = self._client.request(method, url, headers=self._headers(), json=json)
        except httpx.ConnectError as exc:
            raise ProviderUnavailable(f"Azure avatar endpoint unreachable: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Azure avatar request failed: {exc.__class__.__name__}") from exc
        if response.status_code in (401, 403):
            raise ProviderUnavailable(f"Azure avatar refused the credentials (HTTP {response.status_code})")
        if response.status_code == 404 and method == "GET":
            raise ProviderError("Azure avatar job not found")
        if response.status_code >= 400:
            detail = response.text[:200].replace("\n", " ")
            raise ProviderError(f"Azure avatar returned HTTP {response.status_code}: {detail}")
        return response

    # --- renderer ---------------------------------------------------------------------------------------

    def request_body(self, request: VideoRequest) -> dict[str, Any]:
        return {
            "description": request.title[:120],
            "inputKind": "SSML",
            "inputs": [{"content": script_ssml(request, request.voice or self.voice)}],
            "avatarConfig": {
                "talkingAvatarCharacter": self.character,
                "talkingAvatarStyle": self.style,
                "customized": False,
                "videoFormat": "mp4",
                "videoCodec": "h264",
                "subtitleType": "soft_embedded",
                "backgroundColor": self.background,
                "bitrateKbps": self.bitrate_kbps,
            },
            "properties": {"timeToLiveInHours": self.time_to_live_hours},
        }

    def start(self, request: VideoRequest, *, request_id: str = "") -> str:
        if not request.scenes:
            raise ProviderError("nothing to render")
        job_id = f"dlp-{uuid.uuid4().hex}"
        self._call("PUT", self._url(job_id), json=self.request_body(request))
        return job_id

    def status(self, job_id: str) -> VideoJobStatus:
        data = self._call("GET", self._url(job_id)).json()
        return parse_status(data)

    def fetch(self, job_id: str, destination: Path) -> None:
        data = self._call("GET", self._url(job_id)).json()
        result_url = str((data.get("outputs") or {}).get("result") or "")
        if not result_url:
            raise ProviderError("Azure avatar job has no result to download")
        started = time.monotonic()
        try:
            # The result URL is signed; it must not receive the service credentials.
            with self._client.stream("GET", result_url, headers={"User-Agent": USER_AGENT}) as response:
                if response.status_code >= 400:
                    raise ProviderError(f"Azure avatar result download returned HTTP {response.status_code}")
                with destination.open("wb") as handle:
                    for chunk in response.iter_bytes(1024 * 256):
                        handle.write(chunk)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Azure avatar result download failed: {exc.__class__.__name__}") from exc
        if destination.stat().st_size < 1024:
            raise ProviderError("Azure avatar result is empty")
        self.last_download_ms = int((time.monotonic() - started) * 1000)

    def cleanup(self, job_id: str) -> None:
        try:
            self._client.delete(self._url(job_id), headers=self._headers())
        except Exception:  # noqa: BLE001 - best effort; the job expires by itself
            pass


def parse_status(data: dict[str, Any]) -> VideoJobStatus:
    status = str(data.get("status", "")).lower()
    properties = data.get("properties") or {}
    duration = next((int(v) for k, v in properties.items() if k.lower() == "durationinmilliseconds" and v), 0)
    if status == "succeeded":
        return VideoJobStatus("succeeded", duration_ms=duration)
    if status == "failed":
        error = properties.get("error") or data.get("error") or {}
        detail = error.get("message", "") if isinstance(error, dict) else str(error)
        return VideoJobStatus("failed", detail=str(detail)[:200])
    if status == "running":
        return VideoJobStatus("running")
    return VideoJobStatus("pending", detail=status)
