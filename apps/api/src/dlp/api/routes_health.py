from __future__ import annotations

import os
from pathlib import Path

from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text

from dlp.api.deps import RequestContext, context_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_engine
from dlp.providers.preflight import preflight_as_dicts

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(settings_dep)) -> dict:
    """Liveness only; no authentication, no secrets, no provider calls."""
    return {"status": "ok", "release": "0.2", "phase": "B" if settings.app_env == "production" else "A"}


@router.get("/health/ready")
def ready() -> JSONResponse:
    """Internal readiness: bounded database connection and exact packaged migration head. No provider billing."""
    try:
        api_dir = Path(os.environ.get("DLP_API_DIR", str(Path(__file__).resolve().parents[3]))).resolve()
        scripts = ScriptDirectory(str(api_dir / "migrations"))
        expected = scripts.get_current_head()
        with get_engine().connect() as connection:
            actual = connection.execute(text("select version_num from alembic_version")).scalar_one()
        ok = actual == expected
    except Exception:
        ok = False
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ready" if ok else "not_ready"})


@router.get("/health/preflight")
def preflight(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep)) -> dict:
    return {
        "configuration": settings.redacted_summary(),
        "items": preflight_as_dicts(settings, check_network=True),
        "principal": {"email": ctx.principal.email, "identity_provider": ctx.principal.identity_provider},
        "request_id": ctx.request_id,
    }
