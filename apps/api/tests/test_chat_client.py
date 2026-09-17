import json

import httpx
import pytest
from pydantic import BaseModel

from dlp.providers.base import ChatMessage, ProviderError
from dlp.providers.chat_openai_compatible import ChatEndpoint, OpenAICompatibleChatModel, extract_json_object


class Answer(BaseModel):
    answer: str
    notes: str = ""


def _reply(content: str, *, status: int = 200, usage: bool = True) -> httpx.Response:
    body = {"id": "x", "model": "test-model", "choices": [{"message": {"role": "assistant", "content": content},
                                                          "finish_reason": "stop"}]}
    if usage:
        body["usage"] = {"prompt_tokens": 12, "completion_tokens": 7}
    return httpx.Response(status, json=body)


def _model(handler, *, kind="ollama", max_attempts=3) -> OpenAICompatibleChatModel:
    endpoint = ChatEndpoint(kind=kind, base_url="http://localhost:11434/v1" if kind == "ollama" else "https://res.openai.azure.com",
                            model="test-model", api_key="secret" if kind != "ollama" else "", api_version="2024-10-21")
    return OpenAICompatibleChatModel(endpoint, name="unit", max_attempts=max_attempts,
                                     transport=httpx.MockTransport(handler))


def test_structured_reply_is_validated_and_usage_recorded():
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return _reply('```json\n{"answer": "Kunt u dat herhalen?", "notes": "formal"}\n```')

    result = _model(handler).complete([ChatMessage("user", "hallo")], schema=Answer, prompt_version="unit-v1")
    assert isinstance(result.parsed, Answer) and result.parsed.answer == "Kunt u dat herhalen?"
    assert result.input_tokens == 12 and result.output_tokens == 7 and result.attempts == 1
    assert result.prompt_version == "unit-v1" and result.model == "test-model"
    assert seen[0]["response_format"] == {"type": "json_object"}
    assert seen[0]["messages"][0]["role"] == "system" and "JSON schema" in seen[0]["messages"][0]["content"]
    assert seen[0]["max_tokens"] == 400


def test_invalid_json_triggers_a_repair_attempt():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return _reply("Sorry, hier is geen JSON.")
        body = json.loads(request.content)
        assert "not valid" in body["messages"][-1]["content"]
        return _reply('{"answer": "ok"}')

    result = _model(handler).complete([ChatMessage("user", "x")], schema=Answer)
    assert result.parsed.answer == "ok" and result.attempts == 2


def test_retryable_status_then_success():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _reply("", status=429) if calls == 1 else _reply("Dag!")

    result = _model(handler).complete([ChatMessage("user", "x")])
    assert result.text == "Dag!" and result.attempts == 2


def test_gives_up_after_bounded_attempts():
    def handler(request: httpx.Request) -> httpx.Response:
        return _reply("", status=503)

    with pytest.raises(ProviderError, match="after 2 attempts"):
        _model(handler, max_attempts=2).complete([ChatMessage("user", "x")])


def test_non_retryable_error_fails_immediately():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(ProviderError, match="HTTP 400"):
        _model(handler).complete([ChatMessage("user", "x")])
    assert calls == 1


def test_azure_endpoint_shape_and_key_header():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api-key"] = request.headers.get("api-key")
        captured["authorization"] = request.headers.get("authorization")
        return _reply("ok", usage=False)

    result = _model(handler, kind="azure_openai").complete([ChatMessage("user", "x")])
    assert captured["url"] == "https://res.openai.azure.com/openai/deployments/test-model/chat/completions?api-version=2024-10-21"
    assert captured["api-key"] == "secret" and captured["authorization"] is None
    assert result.input_tokens >= 1 and result.output_tokens >= 1  # estimated when usage is absent


@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ('Here you go: {"a": {"b": [1, 2]}} thanks', {"a": {"b": [1, 2]}}),
    ],
)
def test_extract_json_object(text, expected):
    assert extract_json_object(text) == expected


def test_extract_json_object_rejects_non_objects():
    with pytest.raises(ValueError):
        extract_json_object("[1, 2, 3]")
    with pytest.raises(ValueError):
        extract_json_object("no json here")
