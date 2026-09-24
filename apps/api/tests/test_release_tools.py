from __future__ import annotations

import importlib.util
import io
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


def test_unrelated_redirect_is_not_a_sign_in_wall():
    verify = module("verify_live")
    assert not verify.is_sign_in_wall(302, {"location": "/dashboard"})
    assert verify.is_sign_in_wall(302, {"location": "/.auth/login/aad"})
    assert verify.is_sign_in_wall(403, {})


def test_curriculum_preview_access_requires_an_explicit_existing_account():
    release = module("azure_release")
    api = {"properties": {"template": {"containers": [{"env": [
        {"name": "OWNER_ALLOWLIST", "value": "owner@example.com,student@example.com"},
    ]}]}}}
    assert release.validated_admin_emails(" Owner@Example.com ", api) == "owner@example.com"
    assert release.validated_admin_emails("", api) == ""
    with pytest.raises(RuntimeError, match="allowlist"):
        release.validated_admin_emails("stranger@example.com", api)


def ci_run(*, number=1, sha="a" * 40, status="completed", conclusion="success", branch="main", event="push"):
    return {"id": number, "created_at": f"2026-09-24T12:{number:02d}:00Z", "head_sha": sha,
            "status": status, "conclusion": conclusion, "head_branch": branch, "event": event}


def test_release_ci_uses_exact_commit_and_latest_run(monkeypatch):
    release = module("azure_release")
    runs = [ci_run(number=1), ci_run(number=2)]
    requests = []
    def fetch(request, timeout):
        requests.append(request)
        assert timeout == 30
        return io.StringIO(json.dumps({"workflow_runs": runs}))
    monkeypatch.setattr(release, "urlopen", fetch)
    release.verify_commit_ci("owner/repository", "a" * 40, token="test-token")
    assert requests[0].full_url.endswith("?head_sha=" + "a" * 40 + "&event=push&branch=main&per_page=100")
    assert requests[0].get_header("Authorization") == "Bearer test-token"
    # A previous success does not authorize release during a rerun or after a newer failure.
    runs[1]["status"] = "in_progress"
    with pytest.raises(RuntimeError, match="has not succeeded"):
        release.verify_commit_ci("owner/repository", "a" * 40)
    runs[1].update(status="completed", conclusion="failure")
    with pytest.raises(RuntimeError, match="has not succeeded"):
        release.verify_commit_ci("owner/repository", "a" * 40)


@pytest.mark.parametrize("runs", [
    [], [ci_run(sha="b" * 40)], [ci_run(branch="feature")], [ci_run(event="pull_request")],
    [ci_run(status="queued", conclusion=None)], [ci_run(conclusion="cancelled")],
])
def test_release_ci_refuses_unverified_commit(monkeypatch, runs):
    release = module("azure_release")
    monkeypatch.setattr(release, "urlopen", lambda *a, **kw: io.StringIO(json.dumps({"workflow_runs": runs})))
    with pytest.raises(RuntimeError, match="has not succeeded"):
        release.verify_commit_ci("owner/repository", "a" * 40)


def test_release_ci_lookup_failure_is_closed_and_does_not_echo_token(monkeypatch):
    release = module("azure_release")
    def unavailable(*args, **kwargs):
        raise release.URLError("test-token must not be echoed")
    monkeypatch.setattr(release, "urlopen", unavailable)
    monkeypatch.setattr(release, "az", lambda *args: pytest.fail("Azure called before successful CI verification"))
    monkeypatch.setenv("GH_TOKEN", "test-token")
    monkeypatch.setattr(sys, "argv", ["azure_release.py", "verify-ci", "--repository", "owner/repository",
                                      "--commit", "a" * 40])
    assert release.main() == 1
    with pytest.raises(RuntimeError, match="Could not verify GitHub CI") as error:
        release.verify_commit_ci("owner/repository", "a" * 40, token="test-token")
    assert "test-token" not in str(error.value)


@pytest.mark.parametrize("image", [
    "registry.azurecr.io/dlp-api:latest", "registry.azurecr.io/dlp-api:abc123",
    "registry.azurecr.io/dlp-api@sha256:short", "dlp-api@sha256:" + "a" * 64,
    "registry.azurecr.io/dlp-api@sha256:" + "G" * 64,
])
def test_release_refuses_mutable_or_invalid_images_before_azure(monkeypatch, image):
    release = module("azure_release")
    monkeypatch.setattr(release, "az", lambda *args: pytest.fail("Azure called for an invalid image"))
    with pytest.raises(RuntimeError, match="@sha256"):
        release.run_migration("group", "dlp", image)
    monkeypatch.setattr(sys, "argv", ["azure_release.py", "deploy", "--resource-group", "group",
                                      "--api-image", image, "--web-image", "registry.azurecr.io/dlp-web@sha256:" + "b" * 64])
    assert release.main() == 1


def test_release_accepts_only_full_image_digest():
    release = module("azure_release")
    image = "registry.azurecr.io/dlp-api@sha256:" + "a" * 64
    assert release.validate_image(image) == image


@pytest.mark.parametrize("admin", [None, "owner@example.com"])
def test_release_updates_recording_limit_and_only_explicit_preview_identity(monkeypatch, admin):
    release = module("azure_release")
    web = {"properties": {"configuration": {"ingress": {"fqdn": "web.example.test"}}}}
    api = {"properties": {"template": {"containers": [{"env": [
        {"name": "OWNER_ALLOWLIST", "value": "owner@example.com"},
    ]}]}}}
    calls = []
    monkeypatch.setattr(release, "verify_topology", lambda *args: web)
    monkeypatch.setattr(release, "run_migration", lambda *args: calls.append(("migration",)))
    monkeypatch.setattr(release, "wait_for_revision", lambda *args: None)
    def azure(*args):
        calls.append(args)
        return api if args[:2] == ("containerapp", "show") else {}
    monkeypatch.setattr(release, "az", azure)
    argv = ["azure_release.py", "deploy", "--resource-group", "group",
            "--api-image", "registry.azurecr.io/dlp-api@sha256:" + "a" * 64,
            "--web-image", "registry.azurecr.io/dlp-web@sha256:" + "b" * 64]
    if admin:
        argv.extend(["--curriculum-admin-emails", admin])
    monkeypatch.setattr(sys, "argv", argv)
    assert release.main() == 0
    updates = [call for call in calls if call[:2] == ("containerapp", "update")]
    assert len(updates) == 2
    assert calls.index(("migration",)) < calls.index(updates[0])
    assert "MAX_AUDIO_SECONDS=60" in updates[0]
    assert not any("CURRICULUM_ADMIN_EMAILS" in item for item in updates[1])
    assert any("CURRICULUM_ADMIN_EMAILS" in item for item in updates[0]) == bool(admin)
