"""One OpenAI-compatible chat client used for Ollama (Phase A) and Azure (Phase B).

Prompt handling, JSON-schema validation, retries and version tags are identical
for every backend; only the URL and the authentication header differ.
"""

from __future__ import annotations

import json
import logging
import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ValidationError

from dlp.providers.base import ChatMessage, ChatModel, ChatResult, ProviderError, SchemaT

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class ChatEndpoint:
    """Where and how to call the backend."""

    kind: Literal["ollama", "azure_openai"]
    base_url: str
    model: str
    api_key: str = ""
    api_version: str = ""
    timeout_seconds: float = 120.0

    def url(self) -> str:
        base = self.base_url.rstrip("/")
        if self.kind == "azure_openai":
            return f"{base}/openai/deployments/{self.model}/chat/completions?api-version={self.api_version}"
        return f"{base}/chat/completions"

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.kind == "azure_openai":
            headers["api-key"] = self.api_key
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of a reply that may be wrapped in prose or code fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE)
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK.search(stripped)
    if not match:
        raise ValueError("no JSON object in reply")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("JSON reply is not an object")
    return value


def schema_instruction(schema: type[BaseModel]) -> str:
    return (
        "Answer with a single JSON object and nothing else. It must match this JSON schema exactly:\n"
        + json.dumps(schema.model_json_schema(), ensure_ascii=False)
    )


class OpenAICompatibleChatModel(ChatModel):
    def __init__(
        self,
        endpoint: ChatEndpoint,
        *,
        name: str,
        max_attempts: int = 3,
        max_concurrent: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.name = name
        self.model = endpoint.model
        self.max_attempts = max(1, max_attempts)
        self._semaphore = threading.BoundedSemaphore(max(1, max_concurrent))
        self._client = httpx.Client(timeout=endpoint.timeout_seconds, transport=transport)

    def close(self) -> None:
        self._client.close()

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(self.endpoint.url(), headers=self.endpoint.headers(), json=body)
        if response.status_code in RETRYABLE_STATUS:
            raise _Retryable(f"HTTP {response.status_code}")
        if response.status_code >= 400:
            raise ProviderError(f"chat backend returned HTTP {response.status_code}: {response.text[:300]}")
        return response.json()

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
        payload_messages = [{"role": m.role, "content": m.content} for m in messages]
        if schema is not None:
            payload_messages.insert(0, {"role": "system", "content": schema_instruction(schema)})
        body: dict[str, Any] = {
            "model": self.endpoint.model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": int(max_output_tokens),
        }
        if schema is not None:
            body["response_format"] = {"type": "json_object"}

        started = time.monotonic()
        last_error: Exception | None = None
        with self._semaphore:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    data = self._post(body)
                    text = _first_content(data)
                    parsed = None
                    if schema is not None:
                        try:
                            parsed = schema.model_validate(extract_json_object(text))
                        except (ValueError, ValidationError) as exc:
                            # Ask the model to repair its own output once per attempt.
                            body["messages"] = payload_messages + [
                                {"role": "assistant", "content": text},
                                {"role": "user",
                                 "content": f"That was not valid. Error: {exc}. Reply again with only the JSON object."},
                            ]
                            raise _Retryable(f"schema validation failed: {exc.__class__.__name__}") from exc
                    usage = data.get("usage") or {}
                    return ChatResult(
                        text=text,
                        parsed=parsed,
                        provider=self.name,
                        model=str(data.get("model") or self.endpoint.model),
                        prompt_version=prompt_version,
                        input_tokens=int(usage.get("prompt_tokens") or _estimate_tokens(payload_messages)),
                        output_tokens=int(usage.get("completion_tokens") or max(1, len(text) // 4)),
                        latency_ms=int((time.monotonic() - started) * 1000),
                        attempts=attempt,
                        raw={"id": data.get("id"), "finish_reason": _finish_reason(data), "request_id": request_id},
                    )
                except (_Retryable, httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = exc
                    log.warning("chat attempt %s/%s failed (%s): %s", attempt, self.max_attempts, self.name, exc)
                    if attempt < self.max_attempts:
                        time.sleep(random.uniform(0, min(8.0, 0.5 * (2**attempt))))
        raise ProviderError(f"chat call failed after {self.max_attempts} attempts: {last_error}")


class _Retryable(Exception):
    pass


def _first_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("chat backend reply has no choices") from exc
    if content is None:
        return ""
    return str(content)


def _finish_reason(data: dict[str, Any]) -> str:
    try:
        return str(data["choices"][0].get("finish_reason", ""))
    except (KeyError, IndexError, TypeError):
        return ""


def _estimate_tokens(messages: list[dict[str, str]]) -> int:
    return max(1, sum(len(m["content"]) for m in messages) // 4)
