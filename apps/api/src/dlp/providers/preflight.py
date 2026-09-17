"""Reports which providers are configured and reachable. Never prints secrets."""

from __future__ import annotations

import shutil
import socket
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

import httpx
from sqlalchemy import text

from dlp.config import Settings, get_settings
from dlp.db.session import get_engine
from dlp.providers.registry import build_providers


@dataclass
class PreflightItem:
    component: str
    mode: str  # local | azure | fixture | none
    status: str  # ok | missing | unreachable | not_configured | pending_m3
    detail: str


def _tcp_open(url: str, timeout: float = 1.5) -> bool:
    parsed = urlparse(url)
    host, port = parsed.hostname or "localhost", parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run_preflight(settings: Settings | None = None, *, check_network: bool = True) -> list[PreflightItem]:
    settings = settings or get_settings()
    items: list[PreflightItem] = []
    summary = settings.redacted_summary()

    items.append(PreflightItem("environment", settings.app_env, "ok",
                               f"dev_auth={'on' if settings.dev_auth_enabled else 'off'}, allowlist entries={summary['owner_allowlist_size']}"))
    items.append(PreflightItem("assertion key", "shared-secret",
                               "ok" if summary["assertion_key_configured"] else "missing",
                               "at least 32 characters" if summary["assertion_key_configured"] else "ASSERTION_SIGNING_KEY too short"))

    # Database
    try:
        with get_engine().connect() as connection:
            version = connection.execute(text("select version()")).scalar_one()
        items.append(PreflightItem("database", "postgresql", "ok", str(version).split(",")[0][:60]))
    except Exception as exc:  # noqa: BLE001
        items.append(PreflightItem("database", "postgresql", "unreachable", exc.__class__.__name__))

    # ffmpeg
    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        items.append(PreflightItem(tool, "local", "ok" if path else "missing", path or "not on PATH"))

    providers = build_providers(settings)

    # Chat
    if settings.chat_provider == "local":
        reachable = check_network and _tcp_open(settings.local_chat_base_url)
        detail = f"{settings.local_chat_base_url} model={settings.local_chat_model}"
        if reachable:
            try:
                base = settings.local_chat_base_url.rstrip("/").removesuffix("/v1")
                tags = httpx.get(f"{base}/api/tags", timeout=3).json()
                names = [m.get("name") for m in tags.get("models", [])]
                found = settings.local_chat_model in names or any(str(n).startswith(settings.local_chat_model) for n in names)
                detail += f"; installed models: {len(names)}; configured model {'found' if found else 'NOT found'}"
                status = "ok" if found else "missing"
            except Exception:  # noqa: BLE001
                status = "ok"
        else:
            status = "unreachable"
        items.append(PreflightItem("chat model", "local (Ollama)", status, detail))
    elif settings.chat_provider == "azure":
        configured = bool(settings.azure_chat_endpoint and settings.azure_chat_api_key and settings.azure_chat_deployment_small)
        items.append(PreflightItem("chat model", "azure", "ok" if configured else "not_configured",
                                   "endpoint, key and deployments set" if configured else "AZURE_CHAT_* incomplete"))
    else:
        items.append(PreflightItem("chat model", "fixture", "ok", "canned replies; not a verification"))

    # Speech to text
    if settings.stt_provider == "local":
        ok, detail = providers.stt.available()  # type: ignore[attr-defined]
        items.append(PreflightItem("speech to text", "local (faster-whisper)", "ok" if ok else "missing", detail))
    elif settings.stt_provider == "azure":
        ok, detail = providers.stt.available()  # type: ignore[attr-defined]
        items.append(PreflightItem("speech to text", "azure", "pending_m3", detail))
    else:
        items.append(PreflightItem("speech to text", "fixture", "ok", "sidecar transcripts; not a verification"))

    # Text to speech
    if settings.tts_provider == "local":
        ok, detail = providers.tts.available()  # type: ignore[attr-defined]
        items.append(PreflightItem("text to speech", "local (Piper)", "ok" if ok else "missing", detail))
    elif settings.tts_provider == "azure":
        ok, detail = providers.tts.available()  # type: ignore[attr-defined]
        items.append(PreflightItem("text to speech", "azure", "pending_m3", detail))
    else:
        items.append(PreflightItem("text to speech", "fixture", "ok", "tone generator; not a verification"))

    # Blob
    if settings.blob_provider == "memory":
        items.append(PreflightItem("blob store", "memory", "ok", "in-process; not a verification"))
    else:
        mode = "azurite" if settings.blob_provider == "azurite" else "azure"
        if check_network:
            ok, detail = providers.blob.ping()  # type: ignore[attr-defined]
            items.append(PreflightItem("blob store", mode, "ok" if ok else "unreachable", detail))
        else:
            items.append(PreflightItem("blob store", mode, "ok", "network check skipped"))

    items.append(PreflightItem("job loop", "in-process", "ok" if settings.job_loop_enabled else "not_configured",
                               f"poll {settings.job_poll_interval_seconds}s, lease {settings.job_lease_seconds}s"))
    return items


def preflight_as_dicts(settings: Settings | None = None, *, check_network: bool = True) -> list[dict]:
    return [asdict(item) for item in run_preflight(settings, check_network=check_network)]


def format_table(items: list[PreflightItem]) -> str:
    width = max(len(item.component) for item in items)
    lines = [f"{'component'.ljust(width)}  {'mode'.ljust(22)}  {'status'.ljust(14)}  detail",
             f"{'-' * width}  {'-' * 22}  {'-' * 14}  {'-' * 40}"]
    for item in items:
        lines.append(f"{item.component.ljust(width)}  {item.mode.ljust(22)}  {item.status.ljust(14)}  {item.detail}")
    return "\n".join(lines)
