"""Request-scoped dependencies: settings, database session, authenticated learner, request id, CSRF."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from dlp.config import Settings, get_settings
from dlp.db.session import get_session
from dlp.domains.identity.assertions import REQUEST_ID_PATTERN, AssertionError_, Principal, validate_assertion
from dlp.domains.identity.models import Learner
from dlp.domains.identity.service import get_or_create_learner
from dlp.providers.registry import Providers, get_providers

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "fetch"


@dataclass(frozen=True)
class RequestContext:
    principal: Principal
    learner: Learner
    request_id: str


def settings_dep() -> Settings:
    return get_settings()


def providers_dep() -> Providers:
    return get_providers()


def request_id_dep(request: Request, x_request_id: str | None = Header(default=None)) -> str:
    """Use the proxy's request id when it is well-formed; otherwise mint one. Echoed on every response."""
    candidate = (x_request_id or "").strip()
    if not candidate or not REQUEST_ID_PATTERN.match(candidate):
        candidate = uuid.uuid4().hex
    request.state.request_id = candidate
    return candidate


def csrf_dep(request: Request) -> None:
    """State-changing requests must carry the custom header a cross-site form cannot set."""
    if request.method.upper() in UNSAFE_METHODS:
        if request.headers.get(CSRF_HEADER, "").lower() != CSRF_VALUE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="missing anti-CSRF header")


def principal_dep(
    request: Request,
    settings: Settings = Depends(settings_dep),
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="assertion required",
                            headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:].strip()
    try:
        principal = validate_assertion(settings, token)
    except AssertionError_ as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.reason,
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    request.state.principal = principal
    return principal


def context_dep(
    principal: Principal = Depends(principal_dep),
    request_id: str = Depends(request_id_dep),
    _csrf: None = Depends(csrf_dep),
    session: Session = Depends(get_session),
) -> RequestContext:
    learner = get_or_create_learner(session, principal)
    return RequestContext(principal=principal, learner=learner, request_id=request_id)
