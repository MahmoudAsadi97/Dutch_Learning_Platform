"""Deterministic providers for CI and failure injection. They never count as verification."""

from __future__ import annotations

import io
import json
import math
import struct
import time
import wave
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dlp.providers.base import (
    AudioResult,
    BlobStore,
    ChatMessage,
    ChatModel,
    ChatResult,
    ProviderError,
    SchemaT,
    SpeechToText,
    TextToSpeech,
    Transcript,
    TranscriptSegment,
)

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


class FixtureChatModel(ChatModel):
    """Answers from a canned table keyed by prompt version, or a generic JSON reply that fits the schema.

    An entry may be a plain reply, or a rule table `{"rules": [{"any": [..substrings..], "reply": {...}}], "default": {...}}`
    that picks the reply by keywords in the last message (or in the whole prompt with `"match": "all"`), so a
    conversation can be driven deterministically through its phases without a model.
    `fail_first` makes the first N calls raise and `fail_calls` names 1-based call numbers that raise,
    so retry, fallback and usage-release paths can be tested.
    """

    name = "fixture"
    model = "fixture-chat-v1"

    def __init__(self, replies: dict[str, Any] | None = None, *, fail_first: int = 0,
                 fail_calls: tuple[int, ...] = ()) -> None:
        self.replies = replies or _load_json(FIXTURES_DIR / "chat_replies.json")
        self.fail_first = fail_first
        self.fail_calls = set(fail_calls)
        self.calls: list[dict[str, Any]] = []

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
        self.calls.append({"prompt_version": prompt_version, "messages": [m.content for m in messages]})
        if self.fail_first > 0:
            self.fail_first -= 1
            raise ProviderError("injected fixture failure")
        if len(self.calls) in self.fail_calls:
            raise ProviderError("injected fixture failure")
        reply = _select_reply(self.replies.get(prompt_version), messages)
        if reply is None and prompt_version == "curriculum-rubric-v1":
            reply = _curriculum_fixture(messages)
        parsed: BaseModel | None = None
        if schema is not None:
            if isinstance(reply, dict):
                parsed = schema.model_validate(reply)
            else:
                parsed = _example_for(schema)
            text = parsed.model_dump_json()
        else:
            text = reply if isinstance(reply, str) else f"[fixture reply for {prompt_version}]"
        return ChatResult(
            text=text, parsed=parsed, provider=self.name, model=self.model, prompt_version=prompt_version,
            input_tokens=sum(len(m.content) for m in messages) // 4 + 1, output_tokens=len(text) // 4 + 1,
            latency_ms=1, attempts=1, raw={"request_id": request_id},
        )


class FixtureSpeechToText(SpeechToText):
    """Returns the transcript stored in `<wav>.json` next to the recording, or a fixed sentence."""

    name = "fixture"
    model = "fixture-stt-v1"

    def __init__(self, default_text: str = "Ik wil mijn afspraak verzetten.", *, fail_first: int = 0) -> None:
        self.default_text = default_text
        self.fail_first = fail_first

    def transcribe(self, wav_path: Path, *, language: str = "nl", request_id: str = "") -> Transcript:
        if self.fail_first > 0:
            self.fail_first -= 1
            raise ProviderError("injected fixture failure")
        duration = wav_duration_seconds(wav_path)
        sidecar = wav_path.with_suffix(".json")
        text = self.default_text
        if sidecar.exists():
            text = str(json.loads(sidecar.read_text(encoding="utf-8")).get("text", text))
        return Transcript(
            text=text, language=language, duration_seconds=duration, provider=self.name, model=self.model,
            segments=[TranscriptSegment(start=0.0, end=duration, text=text)], confidence=None, latency_ms=1,
        )


class FixtureTextToSpeech(TextToSpeech):
    """Produces a short tone whose length depends on the text, so playback paths can be tested."""

    name = "fixture"
    voice = "fixture-tone"
    label = "synthetic-development"

    def synthesize(self, text: str, *, request_id: str = "") -> AudioResult:
        started = time.monotonic()
        seconds = min(6.0, 0.4 + 0.05 * len(text))
        return AudioResult(
            wav_bytes=tone_wav(seconds), sample_rate=16000, voice=self.voice, provider=self.name,
            label=self.label, latency_ms=int((time.monotonic() - started) * 1000),
        )


class MemoryBlobStore(BlobStore):
    name = "memory"

    def __init__(self) -> None:
        self._data: dict[str, tuple[bytes, str]] = {}

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> None:
        self._data[key] = (bytes(data), content_type)

    def get(self, key: str) -> bytes:
        try:
            return self._data[key][0]
        except KeyError as exc:
            raise ProviderError(f"blob not found: {key}") from exc

    def exists(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def keys(self) -> list[str]:
        return sorted(self._data)


def tone_wav(seconds: float, frequency: float = 440.0, sample_rate: int = 16000) -> bytes:
    frames = int(seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        samples = bytearray()
        for i in range(frames):
            envelope = min(1.0, i / 800, (frames - i) / 800)
            value = int(12000 * envelope * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples += struct.pack("<h", value)
        handle.writeframes(bytes(samples))
    return buffer.getvalue()


def wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate() or 16000)


def _select_reply(entry: Any, messages: list[ChatMessage]) -> Any:
    """Resolve a rule table against the messages; anything that is not a rule table is returned as is."""
    if not isinstance(entry, dict) or "rules" not in entry:
        return entry
    last_raw = messages[-1].content if messages else ""
    last = last_raw.lower()
    everything = "\n".join(m.content for m in messages).lower()
    chosen = entry.get("default")
    for rule in entry.get("rules", []):
        haystack = everything if rule.get("match") == "all" else last
        needles = [str(n).lower() for n in rule.get("any", [])]
        if needles and any(n in haystack for n in needles):
            chosen = rule.get("reply")
            break
    if isinstance(chosen, dict):
        quoted = last_raw.split('"')
        utterance = quoted[1] if len(quoted) >= 3 else last_raw
        chosen = {k: (utterance if v == "$last" else v) for k, v in chosen.items()}
    return chosen


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _example_for(schema: type[BaseModel]) -> BaseModel:
    """Build a minimal instance from field defaults and simple type examples."""
    values: dict[str, Any] = {}
    for name, field in schema.model_fields.items():
        if not field.is_required():
            continue
        annotation = field.annotation
        origin = getattr(annotation, "__origin__", None)
        if annotation is str:
            values[name] = "fixture"
        elif annotation is int:
            values[name] = 0
        elif annotation is float:
            values[name] = 0.0
        elif annotation is bool:
            values[name] = False
        elif origin is list or annotation is list:
            values[name] = []
        elif origin is dict or annotation is dict:
            values[name] = {}
        elif hasattr(annotation, "__args__") and annotation.__args__:
            values[name] = annotation.__args__[0]
        else:
            values[name] = None
    return schema.model_validate(values)


def _curriculum_fixture(messages: list[ChatMessage]) -> dict[str, Any]:
    """Exercise the interface in CI without pretending a fixture validated somebody's language."""
    criteria: list = []
    for message in messages:
        if message.role == "system" and "Criteria: " in message.content:
            criteria = json.loads(message.content.split("Criteria: ", 1)[1].split("\n", 1)[0])
    feedback = {
        "nl": "Testweergave: uw antwoord is opgeslagen, maar uw taal is niet beoordeeld.",
        "en": "Test preview: your answer was saved, but your language was not assessed.",
        "fa": "نمایش آزمایشی: پاسخ ذخیره شد، اما زبان شما ارزیابی نشده است.",
    }
    return {
        "language_is_dutch": False,
        "criteria": [{"criterion_index": index, "met": False, "quote": "", "feedback": feedback}
                     for index in range(len(criteria))],
        "feedback": feedback,
    }
