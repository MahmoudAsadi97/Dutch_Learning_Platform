"""Narrow provider interfaces. Application code depends on these, never on a vendor SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

Role = Literal["system", "user", "assistant"]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class ProviderError(Exception):
    """A provider call failed after its bounded retries."""


class ProviderUnavailable(ProviderError):
    """The provider is not configured or its dependency is not installed."""


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass
class ChatResult:
    text: str
    parsed: BaseModel | None
    provider: str
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    attempts: int
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ChatModel(ABC):
    name: str = "chat"
    model: str = ""

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        *,
        schema: type[SchemaT] | None = None,
        max_output_tokens: int = 400,
        temperature: float = 0.2,
        prompt_version: str = "v0",
        request_id: str = "",
    ) -> ChatResult:
        """Return the model's reply; when `schema` is given the reply must be JSON that validates against it."""

    def complete_once(
        self,
        messages: list[ChatMessage],
        *,
        schema: type[SchemaT] | None = None,
        max_output_tokens: int = 400,
        temperature: float = 0.2,
        prompt_version: str = "v0",
        request_id: str = "",
    ) -> ChatResult:
        """Make one completion without hidden repair, transport or truncation retries.

        Fixture/custom providers may use this fallback only if ``complete`` is
        already a single invocation. Retrying production providers must override
        it with an enforced single-request path. A failure may still be billable;
        callers must retain their conservative usage reservation when uncertain.
        """
        return self.complete(
            messages,
            schema=schema,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            prompt_version=prompt_version,
            request_id=request_id,
        )

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "model": self.model}


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    text: str
    language: str
    duration_seconds: float
    provider: str
    model: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    confidence: float | None = None
    latency_ms: int = 0


class SpeechToText(ABC):
    name: str = "stt"
    model: str = ""

    @abstractmethod
    def transcribe(self, wav_path: Path, *, language: str = "nl", request_id: str = "") -> Transcript:
        """Transcribe a canonical mono 16 kHz 16-bit PCM WAV file."""

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "model": self.model}


@dataclass
class AudioResult:
    wav_bytes: bytes
    sample_rate: int
    voice: str
    provider: str
    label: str  # "synthetic-development" for local voices, "azure-neural" in Phase B
    latency_ms: int = 0


class TextToSpeech(ABC):
    name: str = "tts"
    voice: str = ""
    label: str = "synthetic-development"

    @abstractmethod
    def synthesize(self, text: str, *, request_id: str = "") -> AudioResult:
        """Return mono 16-bit PCM WAV bytes for `text`."""

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "voice": self.voice, "label": self.label}


class BlobStore(ABC):
    name: str = "blob"

    @abstractmethod
    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> None: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name}
