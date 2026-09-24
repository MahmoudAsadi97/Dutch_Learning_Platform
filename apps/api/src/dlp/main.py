"""FastAPI application factory.

The service binds to localhost (or an internal-only ingress in Phase B) and is
reached exclusively through the web app's `/api` proxy. Startup refuses fixture
configuration outside development, logs a redacted preflight, and starts the
bounded job loop.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dlp.api import routes_curriculum, routes_health, routes_missions, routes_practice, routes_progress, routes_speech
from dlp.config import Settings, get_settings
from dlp.domains.jobs.service import JobLoop
from dlp.observability import configure_telemetry, finish_request, request_span
from dlp.providers.preflight import format_table, run_preflight

log = logging.getLogger("dlp")


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    for noisy in ("azure", "azure.core.pipeline.policies.http_logging_policy", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings)
    configure_telemetry(settings)
    if settings.app_env == "production" and settings.dev_auth_enabled:
        raise RuntimeError("refusing to start: fixture identity enabled in production")
    items = run_preflight(settings, check_network=settings.app_env != "test")
    log.info("preflight\n%s", format_table(items))
    loop: JobLoop | None = None
    if settings.job_loop_enabled and settings.app_env != "test":
        loop = JobLoop(settings)
        loop.start()
    app.state.job_loop = loop
    try:
        yield
    finally:
        if loop is not None:
            loop.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Dutch learning platform API",
        version="0.2.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_metadata(request: Request, call_next):
        started = time.monotonic()
        with request_span() as span:
            status = 500
            try:
                response = await call_next(request)
                status = response.status_code
            finally:
                route = getattr(request.scope.get("route"), "path", "unmatched")
                finish_request(span, method=request.method, route=route, status=status,
                               duration=time.monotonic() - started)
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "")
        if request_id:
            response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(int((time.monotonic() - started) * 1000))
        response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        if settings.app_env == "production":
            log.error("unhandled error type=%s request_id=%s", type(exc).__name__,
                      getattr(request.state, "request_id", ""))
        else:
            log.exception("unhandled error on %s %s", request.method, request.url.path)
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(status_code=500, content={"detail": "internal error", "request_id": request_id})

    app.include_router(routes_health.router)
    app.include_router(routes_missions.router)
    app.include_router(routes_practice.router)
    app.include_router(routes_progress.router)
    app.include_router(routes_speech.router)
    app.include_router(routes_curriculum.router)
    return app


app = create_app()
