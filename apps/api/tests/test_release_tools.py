from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("mutation", ["disabled", "empty_allowlist", "open_path", "anonymous", "no_secret"])
def test_publication_refuses_incomplete_auth(mutation):
    release = module("azure_release")
    config = {
        "platform": {"enabled": True},
        "globalValidation": {"unauthenticatedClientAction": "RedirectToLoginPage", "excludedPaths": ["/health"]},
        "identityProviders": {"azureActiveDirectory": {
            "enabled": True, "registration": {"clientSecretSettingName": "auth-client-secret"},
            "validation": {"defaultAuthorizationPolicy": {"allowedPrincipals": {"identities": ["owner-object-id"]}}},
        }},
    }
    assert release.auth_is_restricted(config)
    aad = config["identityProviders"]["azureActiveDirectory"]
    if mutation == "disabled":
        config["platform"]["enabled"] = False
    elif mutation == "empty_allowlist":
        aad["validation"]["defaultAuthorizationPolicy"]["allowedPrincipals"]["identities"] = []
    elif mutation == "open_path":
        config["globalValidation"]["excludedPaths"] = ["/*"]
    elif mutation == "anonymous":
        config["globalValidation"]["unauthenticatedClientAction"] = "AllowAnonymous"
    else:
        aad["registration"] = {}
    assert not release.auth_is_restricted(config)


def test_live_checks_do_not_accept_fixture_or_empty_preflight(monkeypatch):
    verify = module("verify_live")
    for payload in ({}, {"items": [{"component": "chat model", "mode": "fixture", "status": "ok"}]}):
        monkeypatch.setattr(verify, "request", lambda *a, data=payload, **kw: (200, {}, json.dumps(data).encode()))
        assert not verify.signed_in_checks("https://example.invalid", "private-cookie")[0].passed


def test_anonymous_mode_is_explicit_and_never_calls_paid_checks(monkeypatch):
    verify = module("verify_live")
    monkeypatch.setattr(sys, "argv", ["verify_live.py", "--url", "https://example.invalid", "--mode", "anonymous"])
    monkeypatch.setattr(verify, "anonymous_checks", lambda base: [verify.Result("wall", True, "401")])
    monkeypatch.setattr(verify, "signed_in_checks", lambda *args: pytest.fail("paid checks called"))
    assert verify.main() == 0


def test_authenticated_mode_requires_explicit_paid_permission(monkeypatch):
    verify = module("verify_live")
    monkeypatch.setattr(sys, "argv", ["verify_live.py", "--url", "https://example.invalid", "--mode", "authenticated"])
    monkeypatch.delenv("DLP_SESSION_COOKIE", raising=False)
    with pytest.raises(SystemExit) as exc:
        verify.main()
    assert exc.value.code == 2
