"""Guard meaning-specific language guidance and provisional stage design."""

from __future__ import annotations

import json
from pathlib import Path

from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS

ALIGNMENT = Path(__file__).resolve().parents[3] / "content" / "alignment"


def document(name: str) -> dict:
    return json.loads((ALIGNMENT / name).read_text(encoding="utf-8"))


def test_every_stage_has_a_distinct_communication_contract_without_a_certification_claim():
    design = document("learning-design.json")
    levels = document("levels.json")
    assert tuple(stage["id"] for stage in design["stages"]) == STAGE_IDS
    assert design["status"] == "provisional_design_not_calibrated"
    assert len({stage["communicative_focus"] for stage in design["stages"]}) == len(STAGE_IDS)
    assert set(design["source_ids"]) <= {source["id"] for source in levels["sources"]}
    for stage in design["stages"]:
        assert set(stage["four_skill_actions"]) == set(SKILLS)
        assert stage["review_status"] == "provisional_not_human_calibrated"
        assert stage["story_design"]["guidance_is_not_a_cefr_cut_score"] is True
        assert stage["story_design"]["line_count"] == {"min": 8, "max": 12}
    policy = design["collection_policy"]
    assert policy["minimum_stories_per_stage"] >= 200
    assert policy["productive_vocabulary_minimum"] >= 150
    assert policy["preserve_existing_word_bank"] is True
    assert policy["no_cross_stage_story_reuse"] is True


def test_standard_status_depends_on_meaning_and_does_not_invent_a_word_blacklist():
    reference = document("usage-reference.json")
    entries = {entry["id"]: entry for entry in reference["entries"]}
    assert reference["policy"]["automatic_blacklist"] is False
    assert reference["policy"]["meaning_required"] is True
    assert reference["policy"]["register_is_separate_from_standard_status"] is True
    for item in ("plezant-enjoyable", "duimspijker-drawing-pin", "valies-luggage", "kleed-dress"):
        assert entries[item]["status"] == "standard_belgium"
    assert entries["plezant-enjoyable"]["register"] == "informal"
    assert entries["goesting-desire"]["status"] == "uncertain_standard_status_belgium"
    assert entries["tas-bag"]["status"] == "shared_standard"
    assert entries["tas-cup"]["status"] == "nonstandard_in_this_sense"
    assert set(entries["tas-bag"]["forms"]) == set(entries["tas-cup"]["forms"])


def test_both_two_verb_orders_are_accepted_and_the_color_names_are_correct():
    entries = {entry["id"]: entry for entry in document("usage-reference.json")["entries"]}
    participle_first = entries["participle-first-two-verbs"]
    auxiliary_first = entries["auxiliary-first-two-verbs"]
    assert participle_first["status"] == auxiliary_first["status"] == "shared_standard"
    assert participle_first["term"] == "green_order"
    assert auxiliary_first["term"] == "red_order"
    assert participle_first["forms"] == auxiliary_first["shared_standard_alternatives"]
    assert auxiliary_first["forms"] == participle_first["shared_standard_alternatives"]


def test_each_reference_is_sourced_and_support_languages_are_not_mistaken_for_dutch():
    reference = document("usage-reference.json")
    source_ids = {source["id"] for source in reference["sources"]}
    assert len(source_ids) == len(reference["sources"])
    assert len({entry["id"] for entry in reference["entries"]}) == len(reference["entries"])
    for source in reference["sources"]:
        assert source["url"].startswith("https://")
        assert source["checked_at"] == reference["checked_at"]
    for entry in reference["entries"]:
        assert set(entry["source_ids"]) <= source_ids
        assert entry["source_ids"]
        assert set(entry["sense"]) == {"nl", "en", "fa"}
    assert any(item["belgian"] == "remgeld" for item in reference["excluded_equivalences"])
