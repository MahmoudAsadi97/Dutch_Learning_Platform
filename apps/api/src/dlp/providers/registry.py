"""Builds the configured providers. This is the only place that decides local vs Azure vs fixture."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from dlp.config import Settings, get_settings
from dlp.providers.base import BlobStore, ChatModel, ProviderUnavailable, SpeechToText, TextToSpeech
from dlp.providers.blob_azure import AzureBlobStore
from dlp.providers.chat_openai_compatible import ChatEndpoint, OpenAICompatibleChatModel
from dlp.providers.fixtures import FixtureChatModel, FixtureSpeechToText, FixtureTextToSpeech, MemoryBlobStore
from dlp.providers.speech_azure import AzureSpeechToText, AzureTextToSpeech
from dlp.providers.speech_local import FasterWhisperSpeechToText, PiperTextToSpeech


@dataclass
class Providers:
    chat: ChatModel
    chat_strong: ChatModel
    stt: SpeechToText
    tts: TextToSpeech
    blob: BlobStore

    def describe(self) -> dict[str, dict]:
        return {
            "chat": self.chat.describe(),
            "chat_strong": self.chat_strong.describe(),
            "stt": self.stt.describe(),
            "tts": self.tts.describe(),
            "blob": self.blob.describe(),
        }


def _chat_token_provider(scope: str):
    """Lazy SDK construction: configured is not the same as a verified cloud connection."""
    provider = None

    def token() -> str:
        nonlocal provider
        try:
            if provider is None:
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                provider = get_bearer_token_provider(DefaultAzureCredential(), scope)
            return provider()
        except Exception as exc:
            raise ProviderUnavailable("Azure chat identity could not obtain an access token") from exc
    return token


def build_chat(settings: Settings, tier: str = "small") -> ChatModel:
    if settings.chat_provider == "fixture":
        return FixtureChatModel()
    if settings.chat_provider == "azure":
        deployment = (settings.azure_chat_deployment_strong or settings.azure_chat_deployment_small
                      if tier == "strong" else settings.azure_chat_deployment_small)
        endpoint = ChatEndpoint(
            kind="azure_openai", base_url=settings.azure_chat_endpoint, model=deployment or "",
            api_key=settings.azure_chat_api_key, api_version=settings.azure_chat_api_version,
            timeout_seconds=settings.chat_timeout_seconds,
            token_provider=None if settings.azure_chat_api_key else _chat_token_provider(settings.azure_chat_token_scope),
        )
        return OpenAICompatibleChatModel(endpoint, name=f"azure-{tier}", max_attempts=settings.chat_max_attempts,
                                         max_concurrent=settings.max_concurrent_model_calls)
    model = settings.local_chat_model
    if tier == "strong" and settings.local_chat_model_strong:
        model = settings.local_chat_model_strong
    endpoint = ChatEndpoint(kind="ollama", base_url=settings.local_chat_base_url, model=model,
                            timeout_seconds=settings.chat_timeout_seconds)
    return OpenAICompatibleChatModel(endpoint, name=f"local-ollama-{tier}", max_attempts=settings.chat_max_attempts,
                                     max_concurrent=settings.max_concurrent_model_calls)


def _speech_token_provider(settings: Settings):
    """Managed identity (or developer login) tokens when no key is configured; None otherwise."""
    if settings.azure_speech_key or not settings.azure_speech_resource_id:
        return None
    from dlp.providers.speech_azure import managed_identity_token_provider

    try:
        return managed_identity_token_provider()
    except Exception:  # noqa: BLE001 - reported by preflight as not configured
        return None


def build_stt(settings: Settings) -> SpeechToText:
    if settings.stt_provider == "fixture":
        return FixtureSpeechToText()
    if settings.stt_provider == "azure":
        return AzureSpeechToText(settings.azure_speech_key, settings.azure_speech_region, settings.azure_stt_locale,
                                 token_provider=_speech_token_provider(settings), resource_id=settings.azure_speech_resource_id)
    return FasterWhisperSpeechToText(
        model_size=settings.local_stt_model, device=settings.local_stt_device,
        compute_type=settings.local_stt_compute_type, cache_dir=settings.resolve_path(settings.local_stt_cache_dir),
    )


def build_tts(settings: Settings) -> TextToSpeech:
    if settings.tts_provider == "fixture":
        return FixtureTextToSpeech()
    if settings.tts_provider == "azure":
        return AzureTextToSpeech(settings.azure_speech_key, settings.azure_speech_region, settings.azure_tts_voice,
                                 token_provider=_speech_token_provider(settings), resource_id=settings.azure_speech_resource_id)
    return PiperTextToSpeech(voice=settings.local_tts_voice, voices_dir=settings.resolve_path(settings.local_tts_voices_dir))


def build_blob(settings: Settings) -> BlobStore:
    if settings.blob_provider == "memory":
        return MemoryBlobStore()
    if settings.blob_provider == "azure":
        return AzureBlobStore(container=settings.blob_container, account_url=settings.azure_storage_account_url,
                              connection_string=settings.azure_storage_connection_string, name="azure-blob")
    return AzureBlobStore(container=settings.blob_container,
                          connection_string=settings.azure_storage_connection_string, name="azurite")


def build_providers(settings: Settings | None = None) -> Providers:
    settings = settings or get_settings()
    return Providers(
        chat=build_chat(settings, "small"),
        chat_strong=build_chat(settings, "strong"),
        stt=build_stt(settings),
        tts=build_tts(settings),
        blob=build_blob(settings),
    )


@lru_cache(maxsize=1)
def get_providers() -> Providers:
    return build_providers()


def reset_providers() -> None:
    get_providers.cache_clear()
