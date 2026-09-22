"""Verify a deployed environment from the outside (Phase B). Standard library only.

    python scripts/verify_live.py --url https://dlp-web.<region>.azurecontainerapps.io
    DLP_SESSION_COOKIE=... python scripts/verify_live.py --url ... --mode authenticated --allow-paid-smoke

Without a cookie it checks what an anonymous visitor may see: the sign-in wall on the page and on the
API path. API ingress isolation is checked separately by azure_release.py. With a signed-in cookie (copied
from the browser after logging in) it also runs the authenticated checks: preflight reports the Azure
providers, one synthesis carries the `azure-neural` label, usage counters answer, and the acceptance
checks pass. Exit code 0 only when every check passed. Nothing here writes to the environment except
one short synthesis (counted in the usage budget).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

TIMEOUT = 30


@dataclass
class Result:
    name: str
    passed: bool
    detail: str


def request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
            body: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method=method, data=body, headers=headers or {})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read()
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"x-error": str(exc)}, b""


def anonymous_checks(base: str) -> list[Result]:
    results: list[Result] = []
    status, headers, _ = request(base + "/")
    if status == 0:
        return [Result("public entry reachable", False, headers.get("x-error", "unreachable"))]
    results.append(Result("sign-in wall on the page", status in (301, 302, 401, 403),
                          f"HTTP {status}" + (f" → {headers.get('location', '')[:80]}" if "location" in headers else "")))
    status, _, _ = request(base + "/api/health")
    results.append(Result("sign-in wall on the API path", status in (301, 302, 401, 403), f"HTTP {status}"))
    status, headers, _ = request(base + "/api/practice/sessions", method="POST", body=b"{}",
                                 headers={"Content-Type": "application/json"})
    results.append(Result("state change refused anonymously", status in (301, 302, 401, 403), f"HTTP {status}"))
    return results


def signed_in_checks(base: str, cookie: str) -> list[Result]:
    results: list[Result] = []
    common = {"Cookie": cookie, "Accept": "application/json"}

    status, _, body = request(base + "/api/health/preflight", headers=common)
    ok = status == 200
    detail = f"HTTP {status}"
    azure_rows: list[str] = []
    if ok:
        data = json.loads(body)
        items = data.get("items", [])
        for item in items:
            if item.get("mode", "").startswith("azure"):
                azure_rows.append(f"{item['component']}={item['status']}")
        required = {"chat model", "speech to text", "text to speech", "blob store"}
        configured = {i.get("component") for i in items if i.get("mode") == "azure"}
        failing = [i for i in items if i.get("status") not in ("ok", "integration_pending")]
        config = data.get("configuration", {})
        ok = (not failing and required <= configured and config.get("app_env") == "production"
              and config.get("dev_auth_enabled") is False and config.get("paid_usage_enabled") is True)
        detail = ", ".join(azure_rows) or "no azure provider rows"
        if failing:
            detail += "; failing: " + ", ".join(f"{i['component']}={i['status']}" for i in failing)
    results.append(Result("preflight with the Azure providers", ok, detail))

    request_id = uuid.uuid4().hex
    status, headers, body = request(
        base + "/api/speech/synthesize", method="POST",
        headers={**common, "Content-Type": "application/json", "X-Requested-With": "fetch", "X-Request-Id": request_id},
        body=json.dumps({"text": "Goeiedag, u spreekt met Tandartspraktijk Molenstraat."}).encode("utf-8"),
    )
    label = headers.get("x-audio-label", "")
    results.append(Result("one synthesis through the proxy", status == 200 and body[:4] == b"RIFF",
                          f"HTTP {status}, {len(body)} bytes, label {label or '-'}"))
    results.append(Result("synthesis is the Azure voice", label == "azure-neural", f"label {label or '-'}"))

    status, _, body = request(base + "/api/usage", headers=common)
    ok = status == 200 and "counters" in (json.loads(body) if status == 200 else {})
    results.append(Result("usage counters answer", ok, f"HTTP {status}"))

    status, _, body = request(base + "/api/missions/appointment-change/acceptance/all", headers=common)
    passed = status == 200 and json.loads(body).get("passed") is True
    detail = f"HTTP {status}"
    if status == 200:
        checks = json.loads(body).get("checks", [])
        detail += ": " + ", ".join(f"{c['check_id']}={'PASS' if c['passed'] else 'FAIL'}" for c in checks)
    results.append(Result("acceptance checks A01–A06", passed, detail))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True, help="public URL of the web app, without a trailing slash")
    parser.add_argument("--mode", choices=["anonymous", "authenticated"], default="anonymous")
    parser.add_argument("--allow-paid-smoke", action="store_true", help="authorise one budgeted short synthesis")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("--url must be an HTTPS origin without credentials, query or fragment")
    cookie = os.environ.get("DLP_SESSION_COOKIE", "")
    if args.mode == "authenticated" and (not cookie or not args.allow_paid_smoke):
        parser.error("authenticated mode requires DLP_SESSION_COOKIE and --allow-paid-smoke")

    results = anonymous_checks(base)
    if args.mode == "authenticated":
        try:
            results.extend(signed_in_checks(base, cookie))
        except (ValueError, TypeError, KeyError):
            results.append(Result("authenticated response format", False, "unexpected JSON response"))

    width = max(len(r.name) for r in results)
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name.ljust(width)}  {r.detail}")
    passed = all(r.passed for r in results)
    print(f"verify_live ({args.mode} scope only):", "PASS" if passed else "FAIL")
    print("Model conversation, microphone STT, physical phone, content review and recovery drill require the GO_LIVE checklist.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
