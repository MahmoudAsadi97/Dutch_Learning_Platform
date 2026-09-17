"""Operational commands: `python -m dlp.cli <command>`."""

from __future__ import annotations

import argparse
import json
import sys

from dlp.config import get_settings


def cmd_preflight(args: argparse.Namespace) -> int:
    from dlp.providers.preflight import format_table, run_preflight

    items = run_preflight(get_settings(), check_network=not args.offline)
    if args.json:
        print(json.dumps([item.__dict__ for item in items], indent=2))
    else:
        print(format_table(items))
    return 0


def cmd_load_fixture(args: argparse.Namespace) -> int:
    from dlp.db.session import session_scope
    from dlp.domains.content.service import load_all_missions

    with session_scope() as session:
        loaded = load_all_missions(session)
        for mission in loaded:
            print(f"loaded mission {mission.id} v{mission.version} ({mission.fixed_word_count} Dutch words, "
                  f"hash {mission.content_hash[:12]}…, {len(mission.steps)} steps)")
    return 0


def cmd_acceptance(args: argparse.Namespace) -> int:
    from dlp.db.session import session_scope
    from dlp.domains.content.acceptance import check_a01

    checks = {"A01": check_a01}
    if args.check not in checks:
        print(f"unknown check {args.check}; available: {', '.join(checks)}", file=sys.stderr)
        return 2
    with session_scope() as session:
        report = checks[args.check](session, args.mission)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        for item in report.items:
            print(f"[{'PASS' if item.passed else 'FAIL'}] {item.name}  {item.detail}")
        print(f"{report.check_id}: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1


def cmd_run_jobs(args: argparse.Namespace) -> int:
    from dlp.domains.jobs.service import drain

    processed = drain(get_settings(), worker_id="cli", limit=args.limit)
    print(f"processed {processed} job(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dlp")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preflight", help="report configured providers without secrets")
    p.add_argument("--json", action="store_true")
    p.add_argument("--offline", action="store_true", help="skip network reachability checks")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("load-fixture", help="validate and store every mission under content/missions")
    p.set_defaults(func=cmd_load_fixture)

    p = sub.add_parser("acceptance", help="run an acceptance check against the database")
    p.add_argument("--check", default="A01")
    p.add_argument("--mission", default="appointment-change")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_acceptance)

    p = sub.add_parser("run-jobs", help="drain runnable background jobs once")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_run_jobs)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
