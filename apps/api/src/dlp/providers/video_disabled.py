"""A closed rendering port: old configuration cannot accidentally enable paid generation."""
from __future__ import annotations

from pathlib import Path

from dlp.providers.base import ProviderUnavailable, VideoJobStatus, VideoRenderer, VideoRequest


class DisabledVideoRenderer(VideoRenderer):
    name = "disabled"
    label = "retired"

    def start(self, request: VideoRequest, *, request_id: str = "") -> str:
        raise ProviderUnavailable("Video creation has been retired")

    def status(self, job_id: str) -> VideoJobStatus:
        raise ProviderUnavailable("Video creation has been retired")

    def fetch(self, job_id: str, destination: Path) -> None:
        raise ProviderUnavailable("Video creation has been retired")

    def available(self) -> tuple[bool, str]:
        return False, "Video creation removed; narrated stories use text and sentence audio."
