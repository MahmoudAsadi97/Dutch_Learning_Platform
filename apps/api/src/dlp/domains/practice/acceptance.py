"""Acceptance checks A02–A06 over the learner data of a mission.

They are read-only queries against what the application stored, so they can be run at any time
(`python -m dlp.cli acceptance --check all`) and their result is evidence, not a claim:

- A02 four separate skill records per learner and mission, statuses from the allowed set, never merged;
- A03 no speaking record marked practised or passed without spoken (transcript) evidence: typed turns are
  labelled typed evidence and never count as speaking practice;
- A04 every feedback point cites evidence records that exist, belong to the same session and step;
- A05 the checkpoint is independent: no help-ladder use, no typed turn and at most one transfer session
  per learner and mission;
- A06 usage accounting is settled: no reservation left open for more than an hour, no negative counter.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.domains.content.acceptance import CheckReport
from dlp.domains.feedback.models import FeedbackReport
from dlp.domains.practice.models import EvidenceRecord, PracticeSession, PracticeTurn
from dlp.domains.progress.models import SKILLS, SkillRecord
from dlp.domains.usage.models import UsageCounter, UsageReservation

ALLOWED_STATUSES = {"not_started", "in_progress", "practised", "checkpoint_passed"}


def check_a02(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A02", mission_id=mission_id)
    records = list(session.scalars(select(SkillRecord).where(SkillRecord.mission_id == mission_id)))
    by_learner: dict[str, list[SkillRecord]] = {}
    for record in records:
        by_learner.setdefault(str(record.learner_id), []).append(record)
    report.add("learners_with_records", True, f"{len(by_learner)} learner(s), {len(records)} record(s)")
    complete = all(sorted(r.skill for r in items) == sorted(SKILLS) for items in by_learner.values())
    report.add("four_records_per_learner", complete, "one per skill, never merged")
    statuses = {r.status for r in records}
    report.add("statuses_from_allowed_set", statuses <= ALLOWED_STATUSES, ",".join(sorted(statuses)) or "none")
    no_score = all(not any(k in ("score", "level", "cefr") for k in (r.latest_assessment or {})) for r in records)
    report.add("no_score_or_level_stored", no_score, "assessment entries hold step outcomes, not scores")
    return report


def check_a03(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A03", mission_id=mission_id)
    speaking = list(session.scalars(
        select(SkillRecord).where(SkillRecord.mission_id == mission_id, SkillRecord.skill == "speaking")
    ))
    moved = [r for r in speaking if r.status in ("practised", "checkpoint_passed")]
    report.add("speaking_records", True, f"{len(speaking)} record(s), {len(moved)} moved on")
    violations = 0
    for record in moved:
        ids = [i for i in (record.evidence_ids or [])]
        spoken = 0
        if ids:
            spoken = session.scalar(
                select(EvidenceRecord).where(EvidenceRecord.kind == "transcript", EvidenceRecord.id.in_(ids)).limit(1)
            )
        if not spoken:
            violations += 1
    report.add("no_practice_credit_without_spoken_evidence", violations == 0, f"{violations} violation(s)")
    typed_credit = sum(
        1 for r in speaking for step, entry in (r.latest_assessment or {}).items()
        if entry.get("typed_only") and r.status in ("practised", "checkpoint_passed") and not entry.get("spoken")
    )
    report.add("typed_only_steps_not_credited", typed_credit == 0, f"{typed_credit} typed-only step(s) credited")
    return report


def check_a04(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A04", mission_id=mission_id)
    reports = list(session.scalars(
        select(FeedbackReport).join(PracticeSession, PracticeSession.id == FeedbackReport.session_id)
        .where(PracticeSession.mission_id == mission_id)
    ))
    total_points = 0
    bad_points = 0
    for fb in reports:
        evidence = {
            str(e.id): e for e in session.scalars(select(EvidenceRecord).where(EvidenceRecord.session_id == fb.session_id))
        }
        for point in fb.report.get("points", []):
            total_points += 1
            ids = point.get("evidence_ids") or []
            if not ids or any(i not in evidence or evidence[i].step_key != fb.step_key for i in ids):
                bad_points += 1
    report.add("feedback_reports", True, f"{len(reports)} report(s), {total_points} point(s)")
    report.add("every_point_cites_real_evidence_of_its_step", bad_points == 0, f"{bad_points} bad point(s)")
    report.add("dropped_points_recorded", all(isinstance(fb.dropped_points, list) for fb in reports))
    return report


def check_a05(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A05", mission_id=mission_id)
    transfer = list(session.scalars(
        select(PracticeSession).where(PracticeSession.mission_id == mission_id, PracticeSession.variant == "transfer")
    ))
    per_learner: dict[str, int] = {}
    for p in transfer:
        per_learner[str(p.learner_id)] = per_learner.get(str(p.learner_id), 0) + 1
    report.add("transfer_sessions", True, f"{len(transfer)} session(s)")
    report.add("at_most_one_attempt_per_learner", all(n <= 1 for n in per_learner.values()), str(per_learner or {}))
    ids = [p.id for p in transfer]
    help_used = 0
    typed_turns = 0
    if ids:
        help_used = session.scalar(
            select(EvidenceRecord).where(EvidenceRecord.session_id.in_(ids), EvidenceRecord.kind == "help_used").limit(1)
        ) is not None
        typed_turns = session.scalar(
            select(PracticeTurn).where(PracticeTurn.session_id.in_(ids), PracticeTurn.modality == "typed").limit(1)
        ) is not None
    report.add("no_help_in_checkpoint", not help_used)
    report.add("no_typed_turn_in_checkpoint", not typed_turns)
    return report


def check_a06(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A06", mission_id=mission_id)
    stale_before = datetime.now(UTC) - timedelta(hours=1)
    open_old = list(session.scalars(
        select(UsageReservation).where(UsageReservation.state == "reserved", UsageReservation.created_at < stale_before)
    ))
    report.add("no_stale_open_reservations", len(open_old) == 0, f"{len(open_old)} older than one hour")
    negative = list(session.scalars(select(UsageCounter).where((UsageCounter.used < 0) | (UsageCounter.reserved < 0))))
    report.add("no_negative_counters", len(negative) == 0, f"{len(negative)} negative")
    counters = list(session.scalars(select(UsageCounter)))
    over = [c for c in counters if float(c.used) + float(c.reserved) > float(c.limit_value) * 1.5]
    report.add("counters_within_limits", len(over) == 0,
               f"{len(counters)} counter(s); {len(over)} far over their limit (measured usage may exceed a reservation)")
    return report


CHECKS = {"A02": check_a02, "A03": check_a03, "A04": check_a04, "A05": check_a05, "A06": check_a06}
