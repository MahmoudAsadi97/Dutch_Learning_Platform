"""Reference integrity tests; none of these certify the existing language content."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from dlp.domains.curriculum.alignment import AlignmentError, load_alignment, stage_contract, validate_alignment
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS

CONTENT = Path(__file__).resolve().parents[3] / "content"


def documents() -> tuple[dict, dict]:
    data = load_alignment(CONTENT)
    return data["levels"], data["exams"]


def test_alignment_covers_existing_stages_in_order_with_separate_skills():
    levels, _ = documents()
    assert tuple(stage["id"] for stage in levels["stages"]) == STAGE_IDS
    assert levels["assessment_policy"]["open_stage_access"] is True
    for stage in levels["stages"]:
        assert set(stage["skills"]) == set(SKILLS)
        assert stage["review"] == {"status": "provisional", "native_reviewer": None, "content_calibrated": False}
        for skill in SKILLS:
            assert set(stage["skills"][skill]["target"]) == {"nl", "en", "fa"}


def test_official_references_and_internal_bridges_are_not_confused():
    levels, _ = documents()
    by_id = {stage["id"]: stage for stage in levels["stages"]}
    assert by_id["pre-a1"]["reference_status"] == "cefr_descriptor"
    assert by_id["pre-a1"]["bridge_from"] is None
    expected = {"a1": "1.1", "a2": "1.2", "b1": "2", "b2": "3", "c1": "4", "c2": None}
    for stage_id, mapping in expected.items():
        assert by_id[stage_id]["reference_status"] == "cefr_level"
        assert by_id[stage_id]["flemish_mapping"]["richtgraad"] == mapping
    for stage_id, previous in {"pre-a2": "A1", "pre-b1": "A2", "pre-b2": "B1", "pre-c1": "B2", "pre-c2": "C1"}.items():
        assert by_id[stage_id]["reference_status"] == "internal_bridge"
        assert by_id[stage_id]["bridge_from"] == previous
        assert by_id[stage_id]["flemish_mapping"]["richtgraad"] is None


def test_all_sources_are_versioned_authoritative_and_resolve_locally():
    levels, exams = documents()
    for document in (levels, exams):
        assert document["checked_at"] == "2026-10-12"
        source_ids = {source["id"] for source in document["sources"]}
        assert len(source_ids) == len(document["sources"])
        records = document.get("stages", document.get("profiles"))
        for record in records:
            assert set(record["source_ids"]) <= source_ids
    contract = stage_contract("a2", content_dir=CONTENT)
    assert contract["alignment_version"] == levels["version"]
    assert {source["id"] for source in contract["source_details"]} >= set(contract["source_ids"])
    assert {profile["id"] for profile in contract["exam_profiles"]} == set(contract["exam_profile_ids"])


def test_exam_profile_levels_and_format_differences_are_explicit():
    _, exams = documents()
    profiles = {profile["id"]: profile for profile in exams["profiles"]}
    expected_cnavt = {"cnavt-info": "A2", "cnavt-form": "B1", "cnavt-prof": "B2", "cnavt-strt": "B2", "cnavt-edup": "C1"}
    assert {profile_id: profiles[profile_id]["levels"][0] for profile_id in expected_cnavt} == expected_cnavt
    assert profiles["itna-b2"]["levels"] == ["B2"]
    assert profiles["itna-c1"]["levels"] == ["C1"]
    assert "another day" in " ".join(profiles["itna-c1"]["official_format_summary"])
    assert "Word" in profiles["itna-c1"]["permitted_tools_note"]
    assert "Atlas" in " ".join(profiles["certifying-a1-a2"]["official_format_summary"])
    assert "Brussels" in " ".join(profiles["certifying-a1-a2"]["official_format_summary"])
    assert profiles["bosa-professional"]["levels"] == []


def test_c2_has_no_invented_provider_or_certification():
    levels, exams = documents()
    assert levels["assessment_policy"]["recognized_certificate"] is False
    assert levels["assessment_policy"]["cut_scores_validated"] is False
    assert all("C2" not in profile["levels"] for profile in exams["profiles"])
    assert all(profile["recognized_certificate"] is False for profile in exams["profiles"])
    assert all(profile["official_sample_reproduced"] is False for profile in exams["profiles"])
    for stage_id in ("pre-c2", "c2"):
        contract = stage_contract(stage_id, content_dir=CONTENT)
        assert contract["exam_profiles"] == []
        assert contract["exam_coverage_gap"]


@pytest.mark.parametrize("change", [
    "missing_skill", "fake_bridge", "fake_richtgraad", "native_review", "unknown_source", "c2_exam",
])
def test_invalid_alignment_cannot_be_published(change):
    levels, exams = documents()
    if change == "missing_skill":
        del levels["stages"][3]["skills"]["speaking"]
    elif change == "fake_bridge":
        levels["stages"][4]["reference_status"] = "cefr_level"
    elif change == "fake_richtgraad":
        levels["stages"][-1]["flemish_mapping"]["richtgraad"] = "5"
    elif change == "native_review":
        levels["stages"][0]["review"]["native_reviewer"] = "invented approval"
    elif change == "unknown_source":
        levels["stages"][0]["source_ids"] = ["unretrieved-source"]
    elif change == "c2_exam":
        exams["profiles"][0]["levels"].append("C2")
    with pytest.raises(AlignmentError):
        validate_alignment(levels, exams)


def test_source_provenance_and_version_changes_fail_closed():
    levels, exams = documents()
    wrong_url = deepcopy(levels)
    wrong_url["sources"][0]["url"] = "https://unverified-provider.example/levels"
    with pytest.raises(AlignmentError, match="approved authority"):
        validate_alignment(wrong_url, exams)
    exams["version"] = "different-release"
    with pytest.raises(AlignmentError, match="same release"):
        validate_alignment(levels, exams)


def test_stage_contract_is_detached_from_cached_documents_and_unknown_stage_is_rejected():
    changed = stage_contract("b1", content_dir=CONTENT)
    changed["skills"]["reading"]["target"]["nl"] = "changed by caller"
    assert stage_contract("b1", content_dir=CONTENT)["skills"]["reading"]["target"]["nl"] != "changed by caller"
    with pytest.raises(AlignmentError, match="not found"):
        stage_contract("a3", content_dir=CONTENT)


def test_missing_and_malformed_documents_do_not_silently_fall_back(tmp_path):
    with pytest.raises(AlignmentError, match="missing"):
        load_alignment(tmp_path)
    directory = tmp_path / "alignment"
    directory.mkdir()
    (directory / "levels.json").write_text("not json", encoding="utf-8")
    with pytest.raises(AlignmentError, match="invalid JSON"):
        load_alignment(tmp_path)


def test_alternate_content_directory_uses_its_own_release(tmp_path):
    levels, exams = documents()
    directory = tmp_path / "alignment"
    directory.mkdir()
    for name, document in (("levels", levels), ("exams", exams)):
        document["version"] = "alternate-release"
        (directory / f"{name}.json").write_text(json.dumps(document), encoding="utf-8")
    assert stage_contract("a2", content_dir=tmp_path)["alignment_version"] == "alternate-release"
    assert stage_contract("a2", content_dir=CONTENT)["alignment_version"] != "alternate-release"


def test_container_content_directory_override_is_respected(monkeypatch, tmp_path):
    monkeypatch.setenv("DLP_CONTENT_DIR", str(tmp_path))
    with pytest.raises(AlignmentError, match="missing"):
        load_alignment()
    monkeypatch.setenv("DLP_CONTENT_DIR", str(CONTENT))
    assert stage_contract("a1")["flemish_mapping"]["richtgraad"] == "1.1"
