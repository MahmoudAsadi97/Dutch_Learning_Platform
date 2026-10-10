"""Verify a deployed environment from the outside (Phase B). Standard library only.

    python scripts/verify_live.py --url https://dlp-web.<region>.azurecontainerapps.io
    DLP_SESSION_COOKIE=... python scripts/verify_live.py --url ... --mode authenticated --allow-paid-smoke
    DLP_SESSION_COOKIE=... python scripts/verify_live.py --url ... --mode authenticated --allow-paid-smoke --measure-answers

Without a cookie it checks what an anonymous visitor may see: the sign-in wall on the page and on the
API path. API ingress isolation is checked separately by azure_release.py. With a signed-in cookie (copied
from the browser after logging in) it also runs the authenticated checks: preflight reports the Azure
providers, one synthesis carries the `azure-neural` label, usage counters answer, and the acceptance
checks pass. Exit code 0 only when every check passed. Nothing here writes to the environment except
one short synthesis (counted in the usage budget), and with `--measure-answers` one short tap-only practice
session in the signed-in learner's own account (its answers, points and misses stay there; an earlier
measurement session left open is abandoned, a real practice session never is): it times every answer from this
machine through the sign-in proxy over one kept-alive connection and passes when the p95 is at or under 300 ms
(step 3.6).
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

TIMEOUT = 30
ANSWER_P95_MS = 300


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
    status, _, body = request(base + "/health")
    results.append(Result("public web liveness", status == 200 and b'"ok"' in body, f"HTTP {status}"))
    status, headers, _ = request(base + "/")
    if status == 0:
        return [Result("public entry reachable", False, headers.get("x-error", "unreachable"))]
    results.append(Result("sign-in wall on the page", is_sign_in_wall(status, headers),
                          f"HTTP {status}" + (f" → {headers.get('location', '')[:80]}" if "location" in headers else "")))
    status, headers, _ = request(base + "/api/health")
    results.append(Result("sign-in wall on the API path", is_sign_in_wall(status, headers), f"HTTP {status}"))
    status, headers, _ = request(base + "/api/practice/sessions", method="POST", body=b"{}",
                                 headers={"Content-Type": "application/json"})
    results.append(Result("state change refused anonymously", is_sign_in_wall(status, headers), f"HTTP {status}"))
    return results


def is_sign_in_wall(status: int, headers: dict[str, str]) -> bool:
    if status in (401, 403):
        return True
    target = urlparse(headers.get("location", ""))
    return status in (302, 303, 307) and (
        target.path.startswith("/.auth/login/") or target.hostname == "login.microsoftonline.com"
    )


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

    status, _, body = request(base + "/api/health/ready", headers=common)
    results.append(Result("database and migration readiness", status == 200 and b'"ready"' in body, f"HTTP {status}"))

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


def persistent(base: str):
    """One kept-alive HTTPS connection, so a timing is the request itself, not a new TCP and TLS handshake."""
    parsed = urlparse(base)
    connection = http.client.HTTPSConnection(parsed.hostname or "", parsed.port or 443, timeout=TIMEOUT)

    def send(path: str, *, method: str = "GET", headers: dict[str, str] | None = None,
             body: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, {k.lower(): v for k, v in response.getheaders()}, response.read()
        except (http.client.HTTPException, OSError) as exc:
            connection.close()
            return 0, {"x-error": str(exc)}, b""

    return send


def answer_round_trips(base: str, cookie: str) -> Result:
    """One short practice session answered with each item's first option, timing every answer. It asks for
    choice items only, a set the web app never asks for, so it never resumes or abandons a real session."""
    name = f"practice answer round trip p95 <= {ANSWER_P95_MS} ms"
    common = {"Cookie": cookie, "Accept": "application/json", "Content-Type": "application/json",
              "X-Requested-With": "fetch"}
    send = persistent(base)

    def post(path: str, payload: dict) -> tuple[int, dict, float]:
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        status, _, body = send(f"/api/{path}", method="POST", headers={**common, "X-Request-Id": request_id},
                               body=json.dumps({"request_id": request_id, **payload}).encode("utf-8"))
        elapsed = (time.perf_counter() - started) * 1000
        return status, json.loads(body) if status in (200, 201) else {}, elapsed

    send("/api/health/ready", headers=common)  # untimed: opens the connection
    status, view, _ = post("exercises/sessions", {"source": "while_you_wait", "fresh": True, "kinds": ["choice"]})
    if status not in (200, 201):
        return Result(name, False, f"starting a session: HTTP {status}")
    items = {item["id"]: item for item in view["items"]}
    timings: list[float] = []
    next_id = view.get("next_item_id")
    for _ in range(30):
        if not next_id:
            break
        item = items[next_id]
        answer = {"done": True} if item["kind"] == "intro" else {"option": item["prompt"]["options"][0]["id"]}
        status, result, elapsed = post(f"exercises/sessions/{view['id']}/items/{next_id}/answer", {"answer": answer})
        if status != 200:
            return Result(name, False, f"answering: HTTP {status}")
        if item["kind"] != "intro":
            timings.append(elapsed)
        next_id = result.get("next_item_id")
    post(f"exercises/sessions/{view['id']}/finish", {"early": True})
    if not timings:
        return Result(name, False, "no answers were timed")
    ordered = sorted(timings)
    p50 = ordered[max(0, (len(ordered) + 1) // 2 - 1)]
    p95 = ordered[min(len(ordered), -(-95 * len(ordered) // 100)) - 1]
    return Result(name, p95 <= ANSWER_P95_MS, f"{len(timings)} answers, p50 {p50:.0f} ms, p95 {p95:.0f} ms")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True, help="public URL of the web app, without a trailing slash")
    parser.add_argument("--mode", choices=["anonymous", "authenticated"], default="anonymous")
    parser.add_argument("--allow-paid-smoke", action="store_true", help="authorise one budgeted short synthesis")
    parser.add_argument("--measure-answers", action="store_true",
                        help="time one short practice session in the signed-in account (writes its answers)")
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
            if args.measure_answers:
                results.append(answer_round_trips(base, cookie))
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
