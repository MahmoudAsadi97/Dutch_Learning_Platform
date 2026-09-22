"""Application settings.

All configuration comes from environment variables (or a `.env` file at the
repository root). Nothing here reads secrets from anywhere else, and nothing
here prints them: see `redacted_summary()` for what preflight is allowed to show.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parents[4]
# The mission files live next to the applications in the repository; a container image may put them elsewhere.
CONTENT_DIR = Path(os.environ.get("DLP_CONTENT_DIR") or (REPO_ROOT / "content")).resolve()

AppEnv = Literal["development", "test", "production"]
ChatProviderName = Literal["local", "azure", "fixture"]
SpeechProviderName = Literal["local", "azure", "fixture"]
BlobProviderName = Literal["azurite", "azure", "memory"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    # Application
    app_env: AppEnv = "development"
    log_level: str = "INFO"
    paid_usage_enabled: bool = False
    applicationinsights_connection_string: str = Field(default="", repr=False)

    # Identity
    dev_auth_enabled: bool = False
    dev_owner_email: str = "owner@example.com"
    dev_owner_name: str = "Owner"
    owner_allowlist: str = "owner@example.com"
    assertion_signing_key: str = Field(default="", repr=False)
    assertion_issuer: str = "dlp-web"
    assertion_audience: str = "dlp-api"
    assertion_ttl_seconds: int = 60

    # Network
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Database
    database_url: str = Field(default="postgresql+psycopg://dlp:dlp@localhost:5432/dlp", repr=False)
    test_database_url: str = Field(default="postgresql+psycopg://dlp:dlp@localhost:5432/dlp_test", repr=False)

    # Chat
    chat_provider: ChatProviderName = "local"
    local_chat_base_url: str = "http://localhost:11434/v1"
    local_chat_model: str = "llama3.1:8b"
    local_chat_model_strong: str = ""
    chat_timeout_seconds: float = 120.0
    chat_max_output_tokens: int = 600
    # Feedback answers in Dutch and Persian; Persian costs several tokens per word with Llama tokenisers.
    feedback_max_output_tokens: int = 1000
    chat_max_attempts: int = 3
    max_concurrent_model_calls: int = 2
    azure_chat_endpoint: str = ""
    azure_chat_api_key: str = Field(default="", repr=False)
    azure_chat_api_version: str = "v1"
    azure_chat_token_scope: str = "https://ai.azure.com/.default"
    azure_chat_deployment_small: str = ""
    azure_chat_deployment_strong: str = ""

    # Speech to text
    stt_provider: SpeechProviderName = "local"
    local_stt_model: str = "small"
    local_stt_device: str = "cpu"
    local_stt_compute_type: str = "int8"
    local_stt_cache_dir: str = "./.local/whisper"
    azure_speech_key: str = Field(default="", repr=False)
    azure_speech_region: str = ""
    azure_speech_resource_id: str = ""  # set with managed identity instead of a key (Phase B)
    azure_stt_locale: str = "nl-BE"

    # Text to speech
    tts_provider: SpeechProviderName = "local"
    local_tts_voice: str = "nl_BE-nathalie-medium"
    local_tts_voices_dir: str = "./.local/piper-voices"
    azure_tts_voice: str = "nl-BE-DenaNeural"

    # Blob storage
    blob_provider: BlobProviderName = "azurite"
    blob_container: str = "learner-audio"
    azure_storage_connection_string: str = Field(default="", repr=False)
    azure_storage_account_url: str = ""

    # Audio bounds
    max_upload_bytes: int = 5 * 1024 * 1024
    max_audio_seconds: float = 30.0
    ffmpeg_timeout_seconds: float = 20.0
    ffmpeg_memory_limit_mb: int = 2048

    # Usage limits
    usage_daily_model_calls: int = 200
    usage_total_model_calls: int = 5000
    usage_daily_tokens: int = 200_000
    usage_total_tokens: int = 5_000_000
    usage_daily_audio_seconds: int = 1800
    usage_total_audio_seconds: int = 36000

    # Jobs
    job_loop_enabled: bool = True
    job_poll_interval_seconds: float = 2.0
    job_lease_seconds: int = 60
    job_max_attempts: int = 5

    @field_validator("owner_allowlist")
    @classmethod
    def _normalise_allowlist(cls, value: str) -> str:
        return ",".join(sorted({item.strip().lower() for item in value.split(",") if item.strip()}))

    @model_validator(mode="after")
    def _enforce_environment_rules(self) -> Settings:
        if self.app_env == "production":
            if self.dev_auth_enabled:
                raise ValueError("DEV_AUTH_ENABLED must be false when APP_ENV=production")
            if self.chat_provider == "fixture" or self.stt_provider == "fixture" or self.tts_provider == "fixture":
                raise ValueError("fixture providers are not allowed when APP_ENV=production")
            if self.blob_provider == "memory":
                raise ValueError("BLOB_PROVIDER=memory is not allowed when APP_ENV=production")
            if (self.chat_provider, self.stt_provider, self.tts_provider, self.blob_provider) != (
                "azure", "azure", "azure", "azure",
            ):
                raise ValueError("production requires Azure chat, speech and blob providers")
            if not self.paid_usage_enabled:
                raise ValueError("PAID_USAGE_ENABLED must be explicitly approved for production")
            if not self.allowlist or "owner@example.com" in self.allowlist:
                raise ValueError("production requires a real, non-empty OWNER_ALLOWLIST")
            if not (self.azure_chat_endpoint.startswith("https://") and self.azure_chat_deployment_small):
                raise ValueError("Azure chat HTTPS endpoint and small deployment are required")
            if not self.azure_speech_region or not (self.azure_speech_key or self.azure_speech_resource_id):
                raise ValueError("Azure Speech region and key or resource id are required")
            if not self.azure_storage_account_url.startswith("https://"):
                raise ValueError("Azure Storage HTTPS account URL is required")
            database = make_url(self.database_url)
            if database.get_backend_name() != "postgresql" or database.query.get("sslmode") not in (
                "require", "verify-ca", "verify-full",
            ):
                raise ValueError("production PostgreSQL must use TLS")
        if len(self.assertion_signing_key) < 32 and self.app_env == "production":
            raise ValueError("ASSERTION_SIGNING_KEY must be at least 32 characters in production")
        if self.dev_auth_enabled and self.dev_owner_email.lower() not in self.allowlist:
            raise ValueError("DEV_OWNER_EMAIL must be present in OWNER_ALLOWLIST")
        return self

    @property
    def allowlist(self) -> set[str]:
        return {item for item in self.owner_allowlist.split(",") if item}

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def allows_fixture_identity(self) -> bool:
        """Fixture identity exists for the laptop and the test suite only; production refuses it at startup."""
        return self.app_env in ("development", "test") and self.dev_auth_enabled

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (REPO_ROOT / path).resolve()

    def redacted_summary(self) -> dict[str, object]:
        """A description of the configuration that is safe to log or display."""
        return {
            "app_env": self.app_env,
            "dev_auth_enabled": self.dev_auth_enabled,
            "owner_allowlist_size": len(self.allowlist),
            "assertion_key_configured": len(self.assertion_signing_key) >= 32,
            "chat_provider": self.chat_provider,
            "local_chat_model": self.local_chat_model,
            "azure_chat_configured": bool(self.azure_chat_endpoint and self.azure_chat_deployment_small),
            "azure_chat_auth": "key" if self.azure_chat_api_key else "managed_identity",
            "stt_provider": self.stt_provider,
            "azure_speech_configured": bool(
                self.azure_speech_region and (self.azure_speech_key or self.azure_speech_resource_id)
            ),
            "tts_provider": self.tts_provider,
            "blob_provider": self.blob_provider,
            "job_loop_enabled": self.job_loop_enabled,
            "paid_usage_enabled": self.paid_usage_enabled,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
