"""New role invocations cannot silently multiply paid model requests."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import httpx
import pytest
from pydantic import BaseModel

from dlp.providers.base import ChatMessage, ChatModel, ChatResult, ProviderError
from dlp.providers.chat_openai_compatible import ChatEndpoint, OpenAICompatibleChatModel

PRIVATE_TEXT = "private-learner-text-and-credential"


class Answer(BaseModel):
    answer: str


def _reply(content='{"answer":"Dag!"}', *, finish_reason="stop", **overrides):
    payload = {
        "model": "test-model",
        "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 12},
    }
    payload.update(overrides)
    return httpx.Response(200, json=payload)


def _model(handler):
    return OpenAICompatibleChatModel(
        ChatEndpoint(
            kind="azure_openai", base_url="https://unit.invalid", model="test-model",
            api_key=PRIVATE_TEXT, api_version="v1",
        ),
        name="unit", max_attempts=3, transport=httpx.MockTransport(handler),
    )


def test_complete_once_validates_schema_and_preserves_call_options():
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return _reply()

    model = _model(handler)
    try:
        result = model.complete_once(
            [ChatMessage("user", "hello")], schema=Answer, max_output_tokens=123,
            temperature=0.1, prompt_version="bounded-v1", request_id="unit-request",
        )
    finally:
        model.close()
    assert len(bodies) == 1
    assert bodies[0]["max_tokens"] == 123
    assert bodies[0]["temperature"] == 0.1
    assert bodies[0]["response_format"] == {"type": "json_object"}
    assert result.parsed == Answer(answer="Dag!")
    assert result.attempts == 1
    assert result.total_tokens == 32
    assert result.prompt_version == "bounded-v1"
    assert result.raw["request_id"] == "unit-request"
    assert model.max_attempts == 3


@pytest.mark.parametrize("failure", [
    "connect", "timeout", "transport", "429", "503", "400", "redirect", "malformed-envelope",
    "nonobject-envelope", "missing-choices", "invalid-usage", "invalid-json",
    "schema", "truncated",
])
def test_complete_once_never_repairs_or_retries_failures(failure, monkeypatch, caplog):
    requests = []
    sleep = Mock(side_effect=AssertionError("single request must not wait to retry"))
    monkeypatch.setattr("dlp.providers.chat_openai_compatible.time.sleep", sleep)

    def handler(request):
        requests.append(json.loads(request.content))
        if failure in {"connect", "timeout", "transport"}:
            error = {
                "connect": httpx.ConnectError,
                "timeout": httpx.ReadTimeout,
                "transport": httpx.RemoteProtocolError,
            }[failure]
            raise error(PRIVATE_TEXT, request=request)
        if failure in {"429", "503", "400"}:
            return httpx.Response(int(failure), json={"error": PRIVATE_TEXT})
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://other.invalid"})
        if failure == "malformed-envelope":
            return httpx.Response(200, text=PRIVATE_TEXT)
        if failure == "nonobject-envelope":
            return httpx.Response(200, json=[PRIVATE_TEXT])
        if failure == "missing-choices":
            return httpx.Response(200, json={"error": PRIVATE_TEXT})
        if failure == "invalid-usage":
            return _reply(usage={"prompt_tokens": PRIVATE_TEXT})
        if failure == "invalid-json":
            return _reply(PRIVATE_TEXT)
        if failure == "schema":
            return _reply(json.dumps({"answer": {"private": PRIVATE_TEXT}}))
        return _reply('{"answer":"' + PRIVATE_TEXT, finish_reason="length")

    model = _model(handler)
    try:
        with pytest.raises(ProviderError) as exc:
            model.complete_once([ChatMessage("user", "hello")], schema=Answer, max_output_tokens=80)
    finally:
        model.close()
    assert len(requests) == 1
    assert requests[0]["max_tokens"] == 80
    assert len(requests[0]["messages"]) == 2
    assert model.max_attempts == 3
    sleep.assert_not_called()
    assert PRIVATE_TEXT not in str(exc.value)
    assert PRIVATE_TEXT not in caplog.text


def test_legacy_complete_retains_repair_and_truncation_retry(monkeypatch):
    monkeypatch.setattr("dlp.providers.chat_openai_compatible.time.sleep", lambda _: None)
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        if len(bodies) == 1:
            return _reply('{"answer":"unfinished', finish_reason="length")
        if len(bodies) == 2:
            return _reply("not valid JSON")
        return _reply()

    model = _model(handler)
    try:
        result = model.complete([ChatMessage("user", "hello")], schema=Answer, max_output_tokens=80)
    finally:
        model.close()
    assert result.attempts == 3
    assert [body["max_tokens"] for body in bodies] == [80, 160, 160]
    assert "not valid" in bodies[2]["messages"][-1]["content"]


def test_concurrent_single_call_does_not_change_legacy_retry_limit(monkeypatch):
    monkeypatch.setattr("dlp.providers.chat_openai_compatible.time.sleep", lambda _: None)
    barrier = threading.Barrier(2, timeout=10)
    seen = {"single": 0, "legacy": 0}

    def handler(request):
        name = json.loads(request.content)["messages"][-1]["content"]
        seen[name] += 1
        assert model.max_attempts == 3
        if seen[name] == 1:
            barrier.wait()
            return httpx.Response(429, json={"error": "rate limited"})
        return _reply()

    model = _model(handler)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            single = pool.submit(model.complete_once, [ChatMessage("user", "single")], schema=Answer)
            legacy = pool.submit(model.complete, [ChatMessage("user", "legacy")], schema=Answer)
            with pytest.raises(ProviderError):
                single.result(timeout=15)
            assert legacy.result(timeout=15).attempts == 2
    finally:
        model.close()
    assert seen == {"single": 1, "legacy": 2}


def test_legacy_exhausted_schema_error_does_not_expose_model_output(monkeypatch, caplog):
    monkeypatch.setattr("dlp.providers.chat_openai_compatible.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(request)
        return _reply(json.dumps({"answer": {"private": PRIVATE_TEXT}}))

    model = _model(handler)
    try:
        with pytest.raises(ProviderError, match="after 3 attempts") as exc:
            model.complete([ChatMessage("user", "hello")], schema=Answer)
    finally:
        model.close()
    assert len(calls) == 3
    assert PRIVATE_TEXT not in str(exc.value)
    assert PRIVATE_TEXT not in caplog.text


def test_fixture_fallback_delegates_exactly_once_with_all_options():
    class SingleInvocationFixture(ChatModel):
        complete = Mock(return_value=ChatResult("ok", None, "fixture", "fixture", "v1", 0, 0, 0, 1))

    fixture = SingleInvocationFixture()
    messages = [ChatMessage("user", "hello")]
    result = fixture.complete_once(
        messages, schema=Answer, max_output_tokens=45, temperature=0.4,
        prompt_version="v1", request_id="fixture-request",
    )
    assert result.text == "ok"
    fixture.complete.assert_called_once_with(
        messages, schema=Answer, max_output_tokens=45, temperature=0.4,
        prompt_version="v1", request_id="fixture-request",
    )
