"""One set of exception handlers for the API.

A `DomainError` becomes a JSON body with a stable `code`; a provider failure that no route handled
becomes 503 instead of a bare 500. Routes that must commit work before answering (usage rows, a failed
turn) keep returning a `JSONResponse` themselves; these handlers cover everything that is raised.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from dlp.errors import DomainError
from dlp.providers.base import ProviderError, ProviderUnavailable

PROVIDER_UNAVAILABLE = "The language service is temporarily unavailable. Your progress is saved; try again in a moment."


def request_id_of(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "")


def domain_error_response(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.body(request_id_of(request)))


def provider_error_response(request: Request, exc: ProviderError) -> JSONResponse:
    code = "provider_unavailable" if isinstance(exc, ProviderUnavailable) else "provider_failed"
    return JSONResponse(status_code=503, content={"detail": PROVIDER_UNAVAILABLE, "code": code,
                                                  "request_id": request_id_of(request)})


def http_exception_response(request: Request, exc: HTTPException) -> JSONResponse:
    content = {"detail": exc.detail, "request_id": request_id_of(request)}
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


def install_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_response)  # type: ignore[arg-type]
    app.add_exception_handler(ProviderError, provider_error_response)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_response)  # type: ignore[arg-type]
