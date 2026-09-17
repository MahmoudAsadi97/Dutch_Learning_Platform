"""Acceptance check A01: mission fixture integrity.

A01 passes when the mission file on disk validates, the stored copy matches it
byte for byte (content hash), the normalised steps agree with the document, the
fixed Dutch pack is within its word limit, every fixed text still carries a
review status, the four skills are covered, both variants resolve, and the
scenario data the code treats as authoritative (slots, appointment) is coherent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from dlp.domains.content.schemas import SKILLS
from dlp.domains.content.service import (
    MISSIONS_DIR,
    content_hash,
    get_mission,
    mission_document,
    read_mission_file,
    review_summary,
)


@dataclass
class CheckItem:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CheckReport:
    check_id: str
    mission_id: str
    items: list[CheckItem] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.items)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.items.append(CheckItem(name=name, passed=passed, detail=detail))

    def as_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "mission_id": self.mission_id,
            "passed": self.passed,
            "items": [item.__dict__ for item in self.items],
        }


def check_a01(session: Session, mission_id: str = "appointment-change") -> CheckReport:
    report = CheckReport(check_id="A01", mission_id=mission_id)
    path = MISSIONS_DIR / mission_id / "mission.json"
    try:
        on_disk = read_mission_file(path)
        report.add("file_validates", True, str(path.relative_to(path.parents[3])))
    except Exception as exc:  # noqa: BLE001 - the report must describe any failure
        report.add("file_validates", False, str(exc))
        return report

    stored = get_mission(session, mission_id)
    if stored is None:
        report.add("stored_in_database", False, "mission not loaded; run `python -m dlp.cli load-fixture`")
        return report
    report.add("stored_in_database", True, f"version {stored.version}")

    disk_hash = content_hash(on_disk)
    report.add("content_hash_matches", stored.content_hash == disk_hash, f"stored {stored.content_hash[:12]}… disk {disk_hash[:12]}…")

    stored_doc = mission_document(stored)
    report.add("stored_document_validates", content_hash(stored_doc) == disk_hash)

    step_keys_disk = [step.key for step in on_disk.steps]
    step_keys_db = [step.key for step in stored.steps]
    report.add("normalised_steps_match", step_keys_disk == step_keys_db, f"{step_keys_db}")

    words = on_disk.fixed_dutch_word_count()
    limit = on_disk.content_pack.word_limit
    report.add("pack_within_word_limit", words <= limit, f"{words} of {limit} Dutch words")

    summary = review_summary(on_disk)
    report.add("every_text_has_review_status", summary.total_texts > 0, f"{summary.total_texts} texts, {summary.unreviewed} unreviewed")
    report.add("unreviewed_content_is_labelled", stored.review_status == "unreviewed" or summary.unreviewed == 0,
               "mission.review_status reflects the texts")

    covered = {step.skill for step in on_disk.steps}
    report.add("four_skills_covered", covered == set(SKILLS), ",".join(sorted(covered)))

    variants = {scenario.variant for scenario in on_disk.scenarios}
    report.add("base_and_transfer_variants", variants == {"base", "transfer"}, ",".join(sorted(variants)))

    help_ok = True
    for step in on_disk.steps:
        payload = step.payload
        rungs = getattr(payload, "help", None)
        if rungs is not None:
            levels = [rung.level for rung in rungs]
            if levels != sorted(levels) or any(r.kind != "hint_nl" and r.direction != "rtl" for r in rungs):
                help_ok = False
        if payload.type == "checkpoint" and payload.restrictions.help_ladder:
            help_ok = False
    report.add("help_ladder_is_persian_rtl_and_absent_in_checkpoint", help_ok)

    slots_ok = all(
        slot.day >= scenario.reference_date and scenario.appointment.day >= scenario.reference_date
        for scenario in on_disk.scenarios
        for slot in scenario.available_slots
    )
    report.add("authoritative_dates_coherent", slots_ok)
    return report
