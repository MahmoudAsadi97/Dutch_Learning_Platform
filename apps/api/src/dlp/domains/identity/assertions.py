"""Validation of the short-lived assertion the web server attaches to every proxied request.

Trust boundary: the API believes nothing a browser sends. The only identity it
accepts is a JWT signed by the web server with the shared `ASSERTION_SIGNING_KEY`,
carrying the expected issuer and audience, unexpired, and naming a principal on
the owner allowlist. The web server strips client-supplied identity before it
issues the assertion (see `apps/web/lib/assertion.ts`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from dlp.config import Settings

ALGORITHM = "HS256"
IDENTITY_PROVIDERS = ("fixture", "easyauth")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class AssertionError_(Exception):
    """Raised when an assertion is missing, malformed, expired or not allowlisted."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str
    name: str
    identity_provider: str
    request_id: str


def issue_assertion(settings: Settings, *, subject: str, email: str, name: str,
                    identity_provider: str, request_id: str, ttl_seconds: int | None = None,
                    now: datetime | None = None) -> str:
    """Used by tests and tooling; the production issuer is the web server."""
    now = now or datetime.now(UTC)
    ttl = ttl_seconds if ttl_seconds is not None else settings.assertion_ttl_seconds
    claims = {
        "iss": settings.assertion_issuer,
        "aud": settings.assertion_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()) - 5,
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        "sub": subject,
        "email": email,
        "name": name,
        "idp": identity_provider,
        "rid": request_id,
    }
    return jwt.encode(claims, settings.assertion_signing_key, algorithm=ALGORITHM)


def validate_assertion(settings: Settings, token: str) -> Principal:
    if not settings.assertion_signing_key:
        raise AssertionError_("assertion signing key is not configured")
    try:
        claims = jwt.decode(
            token,
            settings.assertion_signing_key,
            algorithms=[ALGORITHM],
            issuer=settings.assertion_issuer,
            audience=settings.assertion_audience,
            leeway=5,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AssertionError_("assertion expired") from exc
    except jwt.PyJWTError as exc:
        raise AssertionError_(f"assertion invalid: {exc.__class__.__name__}") from exc

    lifetime = int(claims["exp"]) - int(claims["iat"])
    if lifetime > max(settings.assertion_ttl_seconds, 1) * 2:
        raise AssertionError_("assertion lifetime too long")

    email = str(claims.get("email", "")).strip().lower()
    subject = str(claims.get("sub", "")).strip()
    idp = str(claims.get("idp", "")).strip()
    request_id = str(claims.get("rid", "")).strip()
    if not email or not subject:
        raise AssertionError_("assertion has no principal")
    if idp not in IDENTITY_PROVIDERS:
        raise AssertionError_("unknown identity provider")
    if idp == "fixture" and not settings.allows_fixture_identity:
        raise AssertionError_("fixture identity is not accepted in this environment")
    if email not in settings.allowlist:
        raise AssertionError_("principal is not on the owner allowlist")
    if request_id and not REQUEST_ID_PATTERN.match(request_id):
        raise AssertionError_("malformed request id")
    return Principal(subject=subject, email=email, name=str(claims.get("name", "")),
                     identity_provider=idp, request_id=request_id)
