"""Bounded Azure release operations. Uses the Azure CLI's configured identity; never reads repository secrets."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time


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
            if (props.get("latestReadyRevisionName") == revision and state.get("healthState") == "Healthy"):
                print(f"{name}: revision ready and healthy.")
                return
            if state.get("provisioningState") in ("Failed", "Deprovisioned"):
                raise RuntimeError(f"{name}: new revision failed; inspect before continuing")
        time.sleep(10)
    raise RuntimeError(f"{name}: readiness timeout; inspect the revision, do not claim deployment success")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["migrate", "verify", "deploy", "publish"])
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--prefix", default="dlp")
    parser.add_argument("--api-image")
    parser.add_argument("--web-image")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9]{2,11}", args.prefix):
        parser.error("prefix must be 3–12 lowercase letters/digits, starting with a letter")
    if args.action == "deploy" and not (args.api_image and args.web_image):
        parser.error("deploy needs both immutable image references")
    try:
        if args.action == "migrate":
            run_migration(args.resource_group, args.prefix, args.api_image)
            return 0
        web = verify_topology(args.resource_group, args.prefix)
        if args.action == "deploy":
            run_migration(args.resource_group, args.prefix, args.api_image)
            for role, image in (("api", args.api_image), ("web", args.web_image)):
                az("containerapp", "update", "-g", args.resource_group, "-n", f"{args.prefix}-{role}", "--image", image)
                wait_for_revision(args.resource_group, f"{args.prefix}-{role}")
        if args.action == "publish":
            for role in ("api", "web"):
                wait_for_revision(args.resource_group, f"{args.prefix}-{role}")
            az("containerapp", "ingress", "enable", "-g", args.resource_group, "-n", f"{args.prefix}-web",
               "--type", "external", "--target-port", "3000", "--transport", "http")
        print("Ingress and sign-in configuration verified. Browser sign-in still requires a real account test.")
        print("Web:", "https://" + web["properties"]["configuration"]["ingress"]["fqdn"])
        return 0
    except (RuntimeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"Release stopped: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
