"""Versioned reference mappings and original readiness designs, never level certification.

This module reads small published JSON files. It makes no database, model or
network calls and does not promote existing content banks to reviewed material.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

STAGE_ORDER = (
    "pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1",
    "pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2",
)
SKILL_ORDER = ("reading", "listening", "speaking", "writing")
CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
FLEMISH_MAPPINGS = {"a1": "1.1", "a2": "1.2", "b1": "2", "b2": "3", "c1": "4", "c2": None}
SOURCE_HOSTS = {
    "rm.coe.int", "www.coe.int", "jaarverslag.ahovoks.be", "eindtermen.vlaanderen.be",
    "www.vlaanderen.be", "nt2-leerdoelen.org", "www.ugent.be", "mijnnederlands.org",
    "www.cll.be", "www.vub.be", "www.itna.be", "www.atlas-antwerpen.be",
    "www.huisnederlandsbrussel.be", "ilt.kuleuven.be", "bosa.belgium.be",
    "uct.ugent.be", "www.uantwerpen.be",
}


class AlignmentError(ValueError):
    """A reference record is absent or violates its publication contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AlignmentError(message)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _localized(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"nl", "en", "fa"} and all(_text(item) for item in value.values())


def _ids(value: Any, available: set[str], label: str, *, allow_empty: bool = False) -> None:
    _require(isinstance(value, list), f"{label} must be a list")
    _require(allow_empty or bool(value), f"{label} must not be empty")
    _require(all(_text(item) and item in available for item in value), f"{label} contains an unknown reference")
    _require(len(set(value)) == len(value), f"{label} contains duplicate references")


def _source_records(document: dict[str, Any], label: str) -> set[str]:
    _require(document.get("schema_version") == 1, f"{label} schema version is unsupported")
    _require(_text(document.get("version")), f"{label} version is missing")
    try:
        checked = date.fromisoformat(document.get("checked_at", ""))
    except (TypeError, ValueError) as exc:
        raise AlignmentError(f"{label} checked_at must be an ISO date") from exc
    _require(checked.isoformat() == document["checked_at"], f"{label} checked_at must be an ISO date")
    sources = document.get("sources")
    _require(isinstance(sources, list) and bool(sources), f"{label} sources are missing")
    ids: set[str] = set()
    for source in sources:
        _require(isinstance(source, dict), f"{label} source must be an object")
        source_id = source.get("id")
        _require(_text(source_id) and source_id not in ids, f"{label} source IDs must be unique")
        ids.add(source_id)
        _require(_text(source.get("title")) and _text(source.get("kind")), f"{label} source details are missing")
        _require(source.get("checked_at") == document["checked_at"], f"{label} source check date is inconsistent")
        _require(_text(source.get("url")), f"{label} source URL is missing")
        parsed = urlsplit(source["url"])
        _require(parsed.scheme == "https" and parsed.hostname in SOURCE_HOSTS
                 and not parsed.username and not parsed.password, f"{label} source URL must identify an approved authority")
    return ids


def validate_alignment(levels: dict[str, Any], exams: dict[str, Any]) -> None:
    """Check structure and provenance. Passing this does not validate language difficulty."""
    _require(isinstance(levels, dict) and isinstance(exams, dict), "alignment documents must be objects")
    level_sources = _source_records(levels, "levels")
    exam_sources = _source_records(exams, "exams")
    _require(levels["version"] == exams["version"] and levels["checked_at"] == exams["checked_at"],
             "alignment documents must use the same release and source-check date")
    _require(levels.get("alignment_status") == "reference_mapped_not_calibrated", "alignment must retain its calibration limit")
    _require(_localized(levels.get("claim")), "levels must state their limited claim in all support languages")
    policy = levels.get("assessment_policy", {})
    _require(policy.get("recognized_certificate") is False and policy.get("cut_scores_validated") is False,
             "alignment cannot assert recognized certificates or validated cut scores")
    _require(policy.get("open_stage_access") is True and policy.get("four_skill_records") is True,
             "alignment must preserve open exploration and separate skills")

    profiles = exams.get("profiles")
    _require(isinstance(profiles, list) and bool(profiles), "exam profiles are missing")
    profile_ids: set[str] = set()
    for profile in profiles:
        _require(isinstance(profile, dict), "exam profile must be an object")
        profile_id = profile.get("id")
        _require(_text(profile_id) and profile_id not in profile_ids, "exam profile IDs must be unique")
        profile_ids.add(profile_id)
        _ids(profile.get("source_ids"), exam_sources, f"exam {profile_id} sources")
        profile_levels = profile.get("levels")
        _require(isinstance(profile_levels, list) and all(level in CEFR_LEVELS for level in profile_levels),
                 "exam profile has an unsupported CEFR level")
        _require("C2" not in profile_levels, "a C2 exam offering has not been verified for this catalog")
        _require(profile.get("recognized_certificate") is False and profile.get("official_sample_reproduced") is False,
                 "readiness profiles cannot issue certificates or reproduce official exam items")
        _require(profile.get("practice_status") == "design_blueprint", "exam practice remains a design blueprint")
        _require(profile.get("checked_at") == exams["checked_at"], "exam profile check date is inconsistent")
        for field in ("title", "family", "purpose", "format_note", "permitted_tools_note"):
            _require(_text(profile.get(field)), f"exam {profile_id} {field} is missing")
        for field in ("official_format_summary", "original_practice_tasks"):
            _require(isinstance(profile.get(field), list) and bool(profile[field])
                     and all(_text(item) for item in profile[field]), f"exam {profile_id} {field} is missing")
    _require(_text(exams.get("coverage_gap", {}).get("C2")), "the C2 exam coverage gap must be explicit")

    stages = levels.get("stages")
    _require(isinstance(stages, list) and all(isinstance(stage, dict) for stage in stages), "stages must be objects")
    _require(tuple(stage.get("id") for stage in stages) == STAGE_ORDER, "the twelve ordered stages must not contain A3")
    profiles_by_id = {profile["id"]: profile for profile in profiles}
    for index, stage in enumerate(stages):
        stage_id = stage["id"]
        _require(stage.get("order") == index + 1, f"stage {stage_id} order is inconsistent")
        _require(stage.get("target_level") in CEFR_LEVELS, f"stage {stage_id} target is invalid")
        _require(_localized(stage.get("purpose")), f"stage {stage_id} purpose requires three languages")
        _require(_text(stage.get("cefr_reference")) and _text(stage.get("task_conditions")),
                 f"stage {stage_id} reference and task conditions are required")
        _ids(stage.get("source_ids"), level_sources, f"stage {stage_id} sources")
        _ids(stage.get("exam_profile_ids"), profile_ids, f"stage {stage_id} exams", allow_empty=True)
        for profile_id in stage["exam_profile_ids"]:
            _require(stage["target_level"] in profiles_by_id[profile_id]["levels"],
                     f"stage {stage_id} references an exam at a different level")
        status = stage.get("reference_status")
        mapping = stage.get("flemish_mapping", {})
        if stage_id == "pre-a1":
            _require(status == "cefr_descriptor" and stage.get("bridge_from") is None
                     and stage["target_level"] == "A1", "Pre-A1 is a descriptor band, not an invented course certificate")
        elif stage_id.startswith("pre-"):
            target = stage_id.removeprefix("pre-").upper()
            previous = CEFR_LEVELS[CEFR_LEVELS.index(target) - 1]
            _require(status == "internal_bridge" and stage["target_level"] == target
                     and stage.get("bridge_from") == previous, f"stage {stage_id} must be an internal bridge")
        else:
            _require(status == "cefr_level" and stage.get("bridge_from") is None
                     and stage["target_level"] == stage_id.upper(), f"stage {stage_id} must retain its CEFR reference")
        _require(mapping.get("richtgraad") == FLEMISH_MAPPINGS.get(stage_id),
                 f"stage {stage_id} has an incorrect Flemish mapping")
        _require(mapping.get("status") == ("reference_mapping" if mapping.get("richtgraad") else "not_an_official_module"),
                 f"stage {stage_id} must not imply an official bridge or C2 module")
        review = stage.get("review", {})
        _require(review.get("status") == "provisional" and review.get("native_reviewer") is None
                 and review.get("content_calibrated") is False, "reference mapping cannot substitute for a human content review")
        skill_records = stage.get("skills")
        _require(isinstance(skill_records, dict) and set(skill_records) == set(SKILL_ORDER),
                 f"stage {stage_id} must cover exactly four skills")
        for skill, record in skill_records.items():
            _require(isinstance(record, dict) and _localized(record.get("target")),
                     f"stage {stage_id} {skill} requires a localized target")
            _require(_text(record.get("practice_task")) and _text(record.get("evidence")),
                     f"stage {stage_id} {skill} requires a task and evidence rule")
        targets = stage.get("provisional_language_targets")
        _require(isinstance(targets, list) and bool(targets) and all(_text(item) for item in targets),
                 f"stage {stage_id} provisional language targets are missing")


@lru_cache(maxsize=8)
def _read_json(path: str, modified: int, size: int) -> dict[str, Any]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AlignmentError("alignment document is missing or invalid JSON") from exc
    _require(isinstance(raw, dict), "alignment document must be an object")
    return raw


def load_alignment(content_dir: Path | None = None) -> dict[str, Any]:
    """Load and validate the two documents; returned data may be safely modified by a caller."""
    directory = content_dir or Path(os.environ.get("DLP_CONTENT_DIR") or Path(__file__).resolve().parents[6] / "content")
    documents: dict[str, Any] = {}
    for name in ("levels", "exams"):
        path = directory / "alignment" / f"{name}.json"
        try:
            stat = path.stat()
        except OSError as exc:
            raise AlignmentError(f"{name} alignment document is missing") from exc
        documents[name] = _read_json(str(path), stat.st_mtime_ns, stat.st_size)
    validate_alignment(documents["levels"], documents["exams"])
    return deepcopy(documents)


def stage_contract(stage_id: str, *, content_dir: Path | None = None) -> dict[str, Any]:
    """Return a sourced stage contract without changing learner progress or review status."""
    documents = load_alignment(content_dir)
    levels, exams = documents["levels"], documents["exams"]
    stage = next((item for item in levels["stages"] if item["id"] == stage_id), None)
    if stage is None:
        raise AlignmentError("learning stage not found")
    wanted_profiles = set(stage["exam_profile_ids"])
    profiles = [profile for profile in exams["profiles"] if profile["id"] in wanted_profiles]
    wanted_sources = set(stage["source_ids"])
    wanted_exam_sources = {source_id for profile in profiles for source_id in profile["source_ids"]}
    return {
        **stage,
        "alignment_version": levels["version"], "checked_at": levels["checked_at"],
        "alignment_status": levels["alignment_status"], "claim": levels["claim"],
        "source_details": [source for source in levels["sources"] if source["id"] in wanted_sources]
        + [source for source in exams["sources"] if source["id"] in wanted_exam_sources],
        "exam_profiles": profiles,
        "exam_coverage_gap": exams["coverage_gap"].get(stage["target_level"]),
    }
