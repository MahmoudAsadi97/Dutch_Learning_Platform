"""Published eligibility skips editorial similarity work only for matching sources."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dlp.domains.curriculum import coverage, reading_manifest
from dlp.domains.curriculum.schemas import STAGE_IDS


def install(root: Path) -> tuple[dict, Path]:
    source = root / "library/a2.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"stories": []}', encoding="utf-8")
    audited = {"stages": [{"stage": stage, **dict.fromkeys(reading_manifest.COUNTS, int(stage == "a2")),
                           "legacy_library_eligible_story_ids": ["a2-eligible"] if stage == "a2" else []}
                          for stage in STAGE_IDS]}
    document = reading_manifest.build(root, audited)
    path = root / reading_manifest.MANIFEST
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(document), encoding="utf-8")
    return document, path


def test_valid_published_manifest_avoids_runtime_similarity_audit(monkeypatch, tmp_path):
    install(tmp_path)
    monkeypatch.setattr(coverage, "CONTENT_DIR", tmp_path)

    def unnecessary_audit(*args):
        raise AssertionError("matching published sources must not repeat the editorial audit")

    monkeypatch.setattr(coverage, "_story_audit", unnecessary_audit)
    assert coverage.eligible_story_ids("a2") == frozenset({"a2-eligible"})
    # An intentionally empty stage is valid, rather than a cache miss.
    assert coverage.eligible_story_ids("c2") == frozenset()
    counts = reading_manifest.stage_counts(tmp_path)
    assert counts["a2"]["eligible_authored_stories"] == 1
    assert counts["c2"]["eligible_authored_stories"] == 0


@pytest.mark.parametrize("relative", ["alignment/story-provenance.json", "study/reading-map.json", "study/reading/c2/01.json",
                                      *[f"{directory}/a2.json" for directory in reading_manifest.DIRECTORIES]])
def test_source_creation_edit_and_deletion_make_manifest_stale(tmp_path, relative):
    _, path = install(tmp_path)
    source = tmp_path / relative
    if source.exists():
        source.unlink()
        path.write_text(json.dumps(reading_manifest.build(tmp_path, {"stages": [
            {"stage": stage, **dict.fromkeys(reading_manifest.COUNTS, 0), "legacy_library_eligible_story_ids": []}
            for stage in STAGE_IDS]})))
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is not None
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("{}")
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is None
    # Regenerating restores the fast path, and a subsequent edit invalidates it.
    document = json.loads(path.read_text())
    document["source_sha256"] = reading_manifest._fingerprint(str(tmp_path), reading_manifest.source_stamp(tmp_path))
    path.write_text(json.dumps(document))
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is not None
    source.write_text('{"changed": true}')
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is None
    document["source_sha256"] = reading_manifest._fingerprint(str(tmp_path), reading_manifest.source_stamp(tmp_path))
    path.write_text(json.dumps(document))
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is not None
    source.unlink()
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is None


@pytest.mark.parametrize("change", ["not_json", "not_object", "extra", "version", "boolean_version", "hash",
                                    "missing_stage", "not_list", "wrong_stage", "duplicate", "non_string",
                                    "negative_count", "boolean_count", "count_mismatch"])
def test_malformed_or_changed_artifact_is_not_trusted(tmp_path, change):
    document, path = install(tmp_path)
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") == frozenset({"a2-eligible"})
    if change == "not_json":
        path.write_text("{")
    elif change == "not_object":
        path.write_text("[]")
    else:
        if change == "extra":
            document["reviewed"] = True
        elif change in {"version", "boolean_version"}:
            document["schema_version"] = 2 if change == "version" else True
        elif change == "hash":
            document["source_sha256"] = "0" * 64
        elif change == "missing_stage":
            del document["stages"]["c2"]
        elif change == "not_list":
            document["stages"]["a2"]["eligible_ids"] = "a2-eligible"
        elif change == "wrong_stage":
            document["stages"]["a2"]["eligible_ids"] = ["c2-eligible"]
        elif change == "duplicate":
            document["stages"]["a2"]["eligible_ids"] *= 2
        elif change in {"negative_count", "boolean_count", "count_mismatch"}:
            document["stages"]["a2"]["counts"]["legacy_library_eligible_stories"] = {
                "negative_count": -1, "boolean_count": True, "count_mismatch": 2}[change]
        else:
            document["stages"]["a2"]["eligible_ids"] = [{}]
        path.write_text(json.dumps(document))
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") is None


def test_missing_or_stale_manifest_falls_back_to_shared_audit(monkeypatch, tmp_path):
    install(tmp_path)
    monkeypatch.setattr(coverage, "CONTENT_DIR", tmp_path)
    calls = []

    def audit(*args):
        calls.append(1)
        return {"stages": [{"stage": "a2", "legacy_library_eligible_story_ids": ["a2-current"]}]}

    monkeypatch.setattr(coverage, "_story_audit", audit)
    (tmp_path / "library/a2.json").write_text('{"edited": true}')
    assert coverage.eligible_story_ids("a2") == frozenset({"a2-current"})
    (tmp_path / reading_manifest.MANIFEST).unlink()
    assert coverage.eligible_story_ids("a2") == frozenset({"a2-current"})
    assert len(calls) == 2


def test_source_fingerprint_survives_checkout_timestamp_changes(tmp_path):
    document, _ = install(tmp_path)
    source = tmp_path / "library/a2.json"
    stat = source.stat()
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert reading_manifest._fingerprint(str(tmp_path), reading_manifest.source_stamp(tmp_path)) == document["source_sha256"]
    assert reading_manifest.eligible_story_ids(tmp_path, "a2") == frozenset({"a2-eligible"})
