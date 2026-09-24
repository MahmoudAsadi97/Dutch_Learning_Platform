"""Bounded Azure release operations. Uses the Azure CLI's configured identity; never reads repository secrets."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def verify_commit_ci(repository: str, commit: str, *, token: str = "") -> None:
    """Require the latest main-push CI run for this exact commit to have succeeded."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repository):
        raise RuntimeError("CI verification requires a GitHub owner/repository")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("CI verification requires a full commit SHA")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "dlp-release",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"https://api.github.com/repos/{repository}/actions/workflows/ci.yml/runs"
        f"?head_sha={commit}&event=push&branch=main&per_page=100", headers=headers,
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        runs = [run for run in payload["workflow_runs"]
                if run.get("head_sha") == commit and run.get("event") == "push" and run.get("head_branch") == "main"]
        latest = max(runs, key=lambda run: (run["created_at"], run["id"])) if runs else None
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as exc:
        # Do not echo HTTP request details: an optional token may be present.
        raise RuntimeError("Could not verify GitHub CI; no release was started") from exc
    if latest is None or latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise RuntimeError("This exact commit's latest main CI run has not succeeded; no release was started")
    print(f"Successful main CI verified for {commit}.")


def validate_image(image: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+@sha256:[0-9a-f]{64}", image):
        raise RuntimeError("Release images must be full registry/repository@sha256:<64 lowercase hex digits> references")
    return image


def az(*args: str):
    result = subprocess.run(["az", *args, "--only-show-errors", "-o", "json"],
                            capture_output=True, text=True, timeout=900, check=False)
    if result.returncode:
        raise RuntimeError(f"Azure command failed: {' '.join(args[:3])}; inspect the resource's deployment status in Azure")
    return json.loads(result.stdout) if result.stdout.strip() else None


def auth_is_restricted(properties: dict) -> bool:
    p = properties.get("properties", properties)
    validation = p.get("globalValidation", {})
    provider = p.get("identityProviders", {}).get("azureActiveDirectory", {})
    policy = provider.get("validation", {}).get("defaultAuthorizationPolicy", {})
    principals = policy.get("allowedPrincipals", {}).get("identities", [])
    return bool(p.get("platform", {}).get("enabled") and provider.get("enabled") and principals
                and validation.get("unauthenticatedClientAction") in ("RedirectToLoginPage", "Return401", "Return403")
                and set(validation.get("excludedPaths", [])) <= {"/health"}
                and provider.get("registration", {}).get("clientSecretSettingName"))


def verify_topology(group: str, prefix: str) -> dict:
    api = az("containerapp", "show", "-g", group, "-n", f"{prefix}-api")
    web = az("containerapp", "show", "-g", group, "-n", f"{prefix}-web")
    if api["properties"]["configuration"]["ingress"].get("external") is not False:
        raise RuntimeError("API ingress must remain internal")
    auth = az("rest", "--method", "get", "--url", f"https://management.azure.com{web['id']}/authConfigs/current?api-version=2024-03-01")
    if not auth_is_restricted(auth):
        raise RuntimeError("Web authentication must be enabled with an explicit principal allowlist; refusing publication")
    for app in (api, web):
        env = {item["name"]: item.get("value") for item in app["properties"]["template"]["containers"][0].get("env", [])}
        if env.get("APP_ENV") != "production" or env.get("DEV_AUTH_ENABLED") != "false":
            raise RuntimeError("Development configuration cannot be published")
    return web


def run_migration(group: str, prefix: str, image: str | None = None) -> None:
    job = f"{prefix}-migrate"
    if image:
        validate_image(image)
        az("containerapp", "job", "update", "-g", group, "-n", job, "--image", image)
    execution = az("containerapp", "job", "start", "-g", group, "-n", job)
    execution_name = execution["name"]
    deadline = time.monotonic() + 960
    while time.monotonic() < deadline:
        state = az("containerapp", "job", "execution", "show", "-g", group, "-n", job, "--job-execution-name", execution_name)
        status = state.get("properties", {}).get("status")
        if status == "Succeeded":
            print("Migration job succeeded.")
            return
        if status in ("Failed", "Stopped", "Degraded"):
            raise RuntimeError(f"Migration job {status}; application images were not changed")
        time.sleep(10)
    raise RuntimeError("Migration job timed out; application images were not changed")


def wait_for_revision(group: str, name: str) -> None:
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        app = az("containerapp", "show", "-g", group, "-n", name)
        props = app["properties"]
        revision = props.get("latestRevisionName")
        if revision:
            state = az("containerapp", "revision", "show", "-g", group, "-n", name, "--revision", revision)["properties"]
            scaled_down = state.get("runningState") == "Stopped" and state.get("healthState") in (None, "None")
            if (props.get("latestReadyRevisionName") == revision
                    and (state.get("healthState") == "Healthy" or scaled_down)):
                print(f"{name}: latest revision ready" + (" (currently scaled to zero)." if scaled_down else " and healthy."))
                return
            if state.get("provisioningState") in ("Failed", "Deprovisioned"):
                raise RuntimeError(f"{name}: new revision failed; inspect before continuing")
        time.sleep(10)
    raise RuntimeError(f"{name}: readiness timeout; inspect the revision, do not claim deployment success")


def validated_admin_emails(value: str, api: dict) -> str:
    """Tester access is explicit and restricted to accounts already allowed into the API."""
    requested = {email.strip().lower() for email in value.split(",") if email.strip()}
    env = {item["name"]: item.get("value", "")
           for item in api["properties"]["template"]["containers"][0].get("env", [])}
    allowed = {email.strip().lower() for email in env.get("OWNER_ALLOWLIST", "").split(",") if email.strip()}
    if not requested <= allowed:
        raise RuntimeError("Tester emails must already be in the verified account allowlist")
    return ",".join(sorted(requested))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["verify-ci", "migrate", "verify", "deploy", "publish"])
    parser.add_argument("--resource-group")
    parser.add_argument("--prefix", default="dlp")
    parser.add_argument("--repository", help="GitHub owner/repository for verify-ci")
    parser.add_argument("--commit", help="Full commit SHA for verify-ci")
    parser.add_argument("--api-image")
    parser.add_argument("--web-image")
    parser.add_argument("--curriculum-admin-emails", default=None,
                        help="Tester emails for locked-stage previews; omitted preserves current access")
    args = parser.parse_args()
    if args.action == "verify-ci" and not (args.repository and args.commit):
        parser.error("verify-ci needs --repository and --commit")
    if args.action != "verify-ci" and not args.resource_group:
        parser.error("--resource-group is required for Azure operations")
    if not re.fullmatch(r"[a-z][a-z0-9]{2,11}", args.prefix):
        parser.error("prefix must be 3–12 lowercase letters/digits, starting with a letter")
    if args.action == "deploy" and not (args.api_image and args.web_image):
        parser.error("deploy needs both immutable image references")
    try:
        if args.action == "verify-ci":
            verify_commit_ci(args.repository, args.commit, token=os.environ.get("GH_TOKEN", ""))
            return 0
        for image in (args.api_image, args.web_image):
            if image:
                validate_image(image)
        if args.action == "migrate":
            run_migration(args.resource_group, args.prefix, args.api_image)
            return 0
        web = verify_topology(args.resource_group, args.prefix)
        if args.action == "deploy":
            admin_emails = None
            if args.curriculum_admin_emails is not None:
                api = az("containerapp", "show", "-g", args.resource_group, "-n", f"{args.prefix}-api")
                admin_emails = validated_admin_emails(args.curriculum_admin_emails, api)
            run_migration(args.resource_group, args.prefix, args.api_image)
            for role, image in (("api", args.api_image), ("web", args.web_image)):
                env_args = ()
                if role == "api":
                    env_args = ("--set-env-vars", "MAX_AUDIO_SECONDS=60")
                    if admin_emails is not None:
                        env_args += (f"CURRICULUM_ADMIN_EMAILS={admin_emails}",)
                az("containerapp", "update", "-g", args.resource_group, "-n", f"{args.prefix}-{role}",
                   "--image", image, *env_args)
                wait_for_revision(args.resource_group, f"{args.prefix}-{role}")
        if args.action == "publish":
            for role in ("api", "web"):
                wait_for_revision(args.resource_group, f"{args.prefix}-{role}")
            az("containerapp", "ingress", "enable", "-g", args.resource_group, "-n", f"{args.prefix}-web",
               "--type", "external", "--target-port", "3000", "--transport", "http")
            web = verify_topology(args.resource_group, args.prefix)
        print("Ingress and sign-in configuration verified. Browser sign-in still requires a real account test.")
        print("Web:", "https://" + web["properties"]["configuration"]["ingress"]["fqdn"])
        return 0
    except (RuntimeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"Release stopped: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
