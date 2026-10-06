#!/usr/bin/env python3
"""Warn before an Azure OpenAI deployment stops serving.

Deployments are pinned (`versionUpgradeOption: NoAutoUpgrade`), so a retired model version simply returns
errors one day. This script lists the account's deployments, looks up each model version's lifecycle in the
region's model catalogue and reports:

  ok         more than --days (default 90) days before the retirement date, and not deprecated
  warning    deprecating (closed to new customers) or retiring within --days days
  retired    deprecated/retired, or the retirement date has passed

Exit codes: 0 ok, 1 warning (0 with --allow-expiring), 2 retired or lookup failed. It uses the Azure CLI's
signed-in identity and prints no secrets. `python -m dlp.cli preflight` reports the same from the optional
AZURE_CHAT_RETIRES_ON setting without any network call.

Usage: python scripts/check_model_lifecycle.py --group dlp-production --account <openai-account> [--location westeurope]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, date, datetime


def az(*args: str) -> object:
    result = subprocess.run(["az", *args, "--only-show-errors", "-o", "json"],
                            capture_output=True, text=True, timeout=300, check=False)
    if result.returncode:
        raise RuntimeError(f"Azure command failed: az {' '.join(args[:3])}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def parse_date(value: object) -> date | None:
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def classify(*, lifecycle: str, retires_on: date | None, today: date, days: int) -> tuple[str, str]:
    """Return (status, detail) for one deployment."""
    status_word = (lifecycle or "").lower()
    if retires_on is not None and retires_on <= today:
        return "retired", f"retirement date {retires_on.isoformat()} has passed"
    if status_word in {"deprecated", "retired"}:
        return "retired", f"lifecycle status {lifecycle}"
    if retires_on is not None and (retires_on - today).days <= days:
        return "warning", f"retires on {retires_on.isoformat()} ({(retires_on - today).days} days)"
    if status_word == "deprecating":
        return "warning", "deprecating: still serving, closed to new deployments"
    detail = f"retires on {retires_on.isoformat()}" if retires_on else "no retirement date published"
    return "ok", detail


def lookup(group: str, account: str, location: str) -> list[dict]:
    deployments = az("cognitiveservices", "account", "deployment", "list", "-g", group, "-n", account) or []
    catalogue = az("cognitiveservices", "model", "list", "-l", location) or []
    by_version: dict[tuple[str, str], dict] = {}
    for entry in catalogue:
        model = entry.get("model", {})
        by_version[(model.get("name", ""), model.get("version", ""))] = model
    rows = []
    for deployment in deployments:
        model = deployment.get("properties", {}).get("model", {})
        key = (model.get("name", ""), model.get("version", ""))
        found = by_version.get(key, {})
        deprecation = found.get("deprecation", {}) or {}
        rows.append({
            "deployment": deployment.get("name", ""),
            "model": key[0], "version": key[1],
            "lifecycle": found.get("lifecycleStatus", "") or "",
            "retires_on": deprecation.get("inference") or "",
            "listed": bool(found),
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", required=True)
    parser.add_argument("--account", required=True, help="the Azure OpenAI account name")
    parser.add_argument("--location", default="westeurope")
    parser.add_argument("--days", type=int, default=90, help="warn when retirement is this close")
    parser.add_argument("--allow-expiring", action="store_true", help="exit 0 on warnings")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = lookup(args.group, args.account, args.location)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"model lifecycle lookup failed: {exc}", file=sys.stderr)
        return 2
    today = datetime.now(UTC).date()
    worst = 0
    for row in rows:
        status, detail = classify(lifecycle=row["lifecycle"], retires_on=parse_date(row["retires_on"]),
                                  today=today, days=args.days)
        if not row["listed"]:
            status, detail = "warning", "model version not found in the region's catalogue"
        row.update({"status": status, "detail": detail})
        worst = max(worst, {"ok": 0, "warning": 1, "retired": 2}[status])
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(f"{row['deployment']:<16} {row['model']} {row['version']:<12} {row['status']:<8} {row['detail']}")
        if not rows:
            print("no deployments found")
    if worst == 1 and args.allow_expiring:
        return 0
    return worst


if __name__ == "__main__":
    sys.exit(main())
