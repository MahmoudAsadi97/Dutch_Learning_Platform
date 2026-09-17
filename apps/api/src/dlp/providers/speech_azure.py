"""Azure Speech adapters (Phase B). Status: not started; implemented and unit-tested against recorded fixtures in M3.

They are declared here so that configuration, preflight and the registry already know
about them. Calling them before M3 raises ProviderUnavailable with a clear message.
"""

from __future__ import annotations

from pathlib import Path

from dlp.providers.base import AudioResult, ProviderUnavailable, SpeechToText, TextToSpeech, Transcript


class AzureSpeechToText(SpeechToText):
    name = "azure-speech"

    def __init__(self, key: str, region: str, locale: str = "nl-BE") -> None:
        self.key = key
        self.region = region
        self.locale = locale
        self.model = f"azure-stt-{locale}"

    def available(self) -> tuple[bool, str]:
        if not (self.key and self.region):
            return False, "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set"
        return False, "adapter scheduled for M3 (integration_pending once written and unit-tested)"

    def transcribe(self, wav_path: Path, *, language: str = "nl", request_id: str = "") -> Transcript:
        raise ProviderUnavailable("Azure Speech recognition adapter is implemented in M3")


class AzureTextToSpeech(TextToSpeech):
    name = "azure-speech"
    label = "azure-neural"

    def __init__(self, key: str, region: str, voice: str = "nl-BE-DenaNeural") -> None:
        self.key = key
        self.region = region
        self.voice = voice

    def available(self) -> tuple[bool, str]:
        if not (self.key and self.region):
            return False, "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set"
        return False, "adapter scheduled for M3 (integration_pending once written and unit-tested)"

    def synthesize(self, text: str, *, request_id: str = "") -> AudioResult:
        raise ProviderUnavailable("Azure Speech synthesis adapter is implemented in M3")
