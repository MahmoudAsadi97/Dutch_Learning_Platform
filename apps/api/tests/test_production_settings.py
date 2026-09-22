import httpx
import pytest

from dlp.config import Settings
from dlp.providers.base import ChatMessage
from dlp.providers.chat_openai_compatible import ChatEndpoint, OpenAICompatibleChatModel
from dlp.providers.registry import build_chat


def production(**overrides):
    values = dict(
        _env_file=None, app_env="production", dev_auth_enabled=False, paid_usage_enabled=True,
        assertion_signing_key="test-signing-material-" * 3, owner_allowlist="learner@example.org",
        chat_provider="azure", stt_provider="azure", tts_provider="azure", blob_provider="azure",
        azure_chat_endpoint="https://sample.openai.azure.com", azure_chat_deployment_small="chat-small",
        azure_speech_region="westeurope", azure_speech_resource_id="/subscriptions/test/resourceGroups/test/speech",
        azure_storage_account_url="https://sample.blob.core.windows.net",
        database_url="postgresql+psycopg://dlp_app:test@database:5432/dlp?sslmode=require",
    )
    return Settings(**{**values, **overrides})


@pytest.mark.parametrize("overrides", [
    {"paid_usage_enabled": False}, {"owner_allowlist": ""}, {"owner_allowlist": "owner@example.com"},
    {"chat_provider": "local"}, {"azure_chat_deployment_small": ""}, {"azure_chat_endpoint": "http://bad"},
    {"azure_speech_region": ""}, {"azure_storage_account_url": "http://bad"},
    {"database_url": "postgresql+psycopg://x:x@database/dlp"},
])
def test_production_fails_closed_when_incomplete(overrides):
    with pytest.raises(ValueError):
        production(**overrides)


def test_managed_identity_configuration_needs_no_chat_key():
    settings = production()
    assert settings.redacted_summary()["azure_chat_configured"]
    assert settings.redacted_summary()["azure_speech_configured"]
    assert build_chat(settings, "strong").model == "chat-small"


def test_managed_identity_is_requested_per_chat_call():
    tokens = iter(["token-one", "token-two"])
    seen = []

    def handler(request):
        seen.append(request.headers["authorization"])
        assert "api-key" not in request.headers
        assert request.url.path == "/openai/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "Hallo"}}]})

    endpoint = ChatEndpoint("azure_openai", "https://sample.openai.azure.com", "small",
                            api_version="v1", token_provider=lambda: next(tokens))
    client = OpenAICompatibleChatModel(endpoint, name="azure-small", transport=httpx.MockTransport(handler))
    try:
        for _ in range(2):
            client.complete([ChatMessage(role="user", content="Hallo")])
        assert seen == ["Bearer token-one", "Bearer token-two"]
    finally:
        client.close()
