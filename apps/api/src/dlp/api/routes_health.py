from __future__ import annotations

from fastapi import APIRouter, Depends

from dlp.api.deps import RequestContext, context_dep, settings_dep
from dlp.config import Settings
from dlp.providers.preflight import preflight_as_dicts

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness only; no authentication, no secrets, no provider calls."""
    return {"status": "ok", "release": "0.1", "phase": "A"}


@router.get("/health/preflight")
def preflight(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep)) -> dict:
    return {
        "configuration": settings.redacted_summary(),
        "items": preflight_as_dicts(settings, check_network=True),
        "principal": {"email": ctx.principal.email, "identity_provider": ctx.principal.identity_provider},
        "request_id": ctx.request_id,
    }
