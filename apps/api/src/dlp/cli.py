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


def cmd_export_recording(args: argparse.Namespace) -> int:
    """Copy a stored learner recording (canonical WAV) plus a transcript sidecar out of the blob store."""
    from pathlib import Path

    from sqlalchemy import select

    from dlp.db.session import session_scope
    from dlp.domains.speech.models import AudioAsset
    from dlp.providers.registry import get_providers

    with session_scope() as session:
        asset = session.scalar(
            select(AudioAsset).where(AudioAsset.request_id == args.request_id, AudioAsset.kind == "recording")
        )
        if asset is None:
            print(f"no recording with request id {args.request_id}", file=sys.stderr)
            return 1
        payload = {
            "text": asset.meta.get("transcript", ""),
            "provider": asset.provider,
            "model": asset.meta.get("stt_model", ""),
            "duration_seconds": asset.duration_seconds,
            "recorded_at": asset.created_at.isoformat(),
            "note": "recorded on the owner's laptop through the microphone check page; may contain personal data",
        }
        wav = get_providers().blob.get(asset.blob_key)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(wav)
    out.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(wav)} bytes, {asset.duration_seconds:.2f} s) and {out.with_suffix('.json').name}")
    print("transcript:", payload["text"])
    return 0


LEARNER_DATA_TABLES = [
    "feedback_reports", "usage_reservations", "usage_counters", "evidence_records", "practice_turns",
    "practice_sessions", "skill_records", "audio_assets", "jobs", "learners",
]


def cmd_reset_learner_data(args: argparse.Namespace) -> int:
    """Empty every learner-generated table. Only for the test database: the name must end in `_test`."""
    from sqlalchemy import text

    from dlp.db.session import get_engine

    settings = get_settings()
    database = settings.database_url.rsplit("/", 1)[-1].split("?")[0]
    if not database.endswith("_test") and not args.force:
        print(f"refusing to reset {database!r}: the database name must end in _test (or pass --force)", file=sys.stderr)
        return 2
    if settings.app_env == "production":
        print("refusing to reset learner data in production", file=sys.stderr)
        return 2
    with get_engine().begin() as connection:
        connection.execute(text("TRUNCATE " + ", ".join(LEARNER_DATA_TABLES) + " CASCADE"))
    print(f"learner data reset in {database}")
    return 0


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

    p = sub.add_parser("export-recording", help="write a stored recording and its transcript sidecar to disk")
    p.add_argument("request_id", help="the request id shown on the microphone check page")
    p.add_argument("--out", default="tests/fixtures/dutch_sentence.wav")
    p.set_defaults(func=cmd_export_recording)

    p = sub.add_parser("reset-learner-data", help="empty the learner-generated tables of the test database")
    p.add_argument("--force", action="store_true", help="allow a database whose name does not end in _test")
    p.set_defaults(func=cmd_reset_learner_data)

    p = sub.add_parser("run-jobs", help="drain runnable background jobs once")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_run_jobs)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
