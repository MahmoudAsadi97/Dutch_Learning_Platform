from datetime import datetime, timedelta, timezone

import jwt
import pytest

from dlp.config import Settings
from dlp.domains.identity.assertions import AssertionError_, issue_assertion, validate_assertion
from tests.conftest import auth_headers


def _settings(**overrides) -> Settings:
    base = {
        "app_env": "development",
        "dev_auth_enabled": True,
        "dev_owner_email": "owner@example.com",
        "owner_allowlist": "owner@example.com",
        "assertion_signing_key": "k" * 40,
    }
    base.update(overrides)
    return Settings(**base)


def _token(settings: Settings, **kwargs) -> str:
    params = {"subject": "fixture:owner@example.com", "email": "owner@example.com", "name": "Owner",
              "identity_provider": "fixture", "request_id": "req-00000001"}
    params.update(kwargs)
    return issue_assertion(settings, **params)


def test_valid_assertion_yields_principal():
    settings = _settings()
    principal = validate_assertion(settings, _token(settings))
    assert principal.email == "owner@example.com"
    assert principal.identity_provider == "fixture"
    assert principal.request_id == "req-00000001"


def test_expired_assertion_is_refused():
    settings = _settings()
    old = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = _token(settings, now=old)
    with pytest.raises(AssertionError_, match="expired"):
        validate_assertion(settings, token)


def test_wrong_audience_and_wrong_key_are_refused():
    settings = _settings()
    other = _settings(assertion_audience="someone-else")
    with pytest.raises(AssertionError_, match="invalid"):
        validate_assertion(settings, _token(other))
    with pytest.raises(AssertionError_, match="invalid"):
        validate_assertion(settings, _token(_settings(assertion_signing_key="x" * 40)))


def test_unlisted_principal_is_refused():
    settings = _settings()
    with pytest.raises(AssertionError_, match="allowlist"):
        validate_assertion(settings, _token(settings, email="intruder@example.com"))


def test_fixture_identity_refused_when_disabled():
    settings = _settings(app_env="test", dev_auth_enabled=False)
    with pytest.raises(AssertionError_, match="fixture identity"):
        validate_assertion(settings, _token(settings))
    # easyauth principals remain valid there
    principal = validate_assertion(settings, _token(settings, identity_provider="easyauth", subject="aad-123"))
    assert principal.subject == "aad-123"


def test_overlong_lifetime_is_refused():
    settings = _settings()
    token = _token(settings, ttl_seconds=3600)
    with pytest.raises(AssertionError_, match="lifetime"):
        validate_assertion(settings, token)


def test_alg_none_is_refused():
    settings = _settings()
    claims = {"iss": settings.assertion_issuer, "aud": settings.assertion_audience, "sub": "x",
              "email": "owner@example.com", "idp": "fixture",
              "iat": int(datetime.now(timezone.utc).timestamp()),
              "exp": int((datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp())}
    token = jwt.encode(claims, key="", algorithm="none")
    with pytest.raises(AssertionError_):
        validate_assertion(settings, token)


def test_production_settings_refuse_fixture_identity():
    with pytest.raises(ValueError, match="DEV_AUTH_ENABLED"):
        Settings(app_env="production", dev_auth_enabled=True, assertion_signing_key="k" * 40,
                 owner_allowlist="owner@example.com", dev_owner_email="owner@example.com")
    with pytest.raises(ValueError, match="fixture providers"):
        Settings(app_env="production", dev_auth_enabled=False, chat_provider="fixture",
                 assertion_signing_key="k" * 40)


def test_api_requires_assertion_and_csrf_header(client):
    assert client.get("/health").status_code == 200
    assert client.get("/progress").status_code == 401
    assert client.get("/progress", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    ok = client.get("/progress", headers=auth_headers())
    assert ok.status_code == 200
    assert ok.headers["x-request-id"] == "test-request-0001"
    denied = client.post("/practice/sessions", headers=auth_headers(csrf=False),
                         json={"mission_id": "appointment-change"})
    assert denied.status_code == 403
    assert client.get("/progress", headers=auth_headers(email="intruder@example.com")).status_code == 401


def test_learner_is_created_once_per_principal(client):
    first = client.get("/progress", headers=auth_headers("test-request-0001")).json()["learner"]
    second = client.get("/progress", headers=auth_headers("test-request-0002")).json()["learner"]
    assert first["id"] == second["id"]
    assert first["email"] == "owner@example.com"
