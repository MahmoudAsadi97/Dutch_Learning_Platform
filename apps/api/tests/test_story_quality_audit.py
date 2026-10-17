"""Editorial audits must detect inflated counts without pretending to judge language."""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "story_quality_audit", Path(__file__).resolve().parents[3] / "scripts/validate_story_quality.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def story(identifier="a1-story-1", prefix=""):
    lines = [{"nl": prefix + f"Sara neemt boek {i} mee naar het park.",
              "en": prefix + f"Sara takes book {i} to the park.",
              "fa": prefix + f"سارا کتاب {i} را به پارک می‌برد."} for i in range(1, 9)]
    return {"id": identifier, "title": {"nl": "Een boek in het park"}, "lines": lines,
            "paragraphs": [{lang: " ".join(line[lang] for line in group) for lang in MODULE.LANGS}
                           for group in (lines[:4], lines[4:])]}


def write_pack(root, stage, stories, directory="library"):
    path = root / directory / f"{stage}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"stage_id": stage, "stories": stories,
                                "vocabulary": [{"term": "het boek"}]}, ensure_ascii=False))


def codes(result):
    return {issue["code"] for issue in result["issues"]}


def test_legacy_and_authored_counts_are_separate(tmp_path):
    modern = story()
    legacy = deepcopy(modern)
    legacy.pop("lines")
    legacy["id"] = "a1-old"
    legacy["paragraphs"][0]["nl"] = "De trein vertrekt te laat. Een reiziger zoekt een andere verbinding."
    legacy["paragraphs"][1]["nl"] = "Aan het loket krijgt hij uitleg. Nu weet hij welk perron hij nodig heeft."
    write_pack(tmp_path, "a1", [legacy])
    write_pack(tmp_path, "a1", [modern], "learning-units")
    row = next(row for row in MODULE.audit(tmp_path)["stages"] if row["stage"] == "a1")
    assert row["stories_total"] == 2
    assert row["authored_stories"] == row["legacy_stories"] == 1
    assert row["authored_story_shortfall"] == 199


@pytest.mark.parametrize("count", [0, 7, 13])
def test_authoring_lines_cannot_fake_the_requested_range(tmp_path, count):
    value = story()
    value["lines"] = (value["lines"] * 2)[:count]
    write_pack(tmp_path, "a1", [value])
    result = MODULE.audit(tmp_path)
    assert "authored_line_count" in codes(result)
    assert next(row for row in result["stages"] if row["stage"] == "a1")["authored_stories"] == 0


def test_line_paragraph_translation_mismatch_detected(tmp_path):
    value = story()
    value["lines"][2]["fa"] = "ترجمه‌ای متفاوت."
    write_pack(tmp_path, "a1", [value])
    result = MODULE.audit(tmp_path)
    issue = next(issue for issue in result["issues"] if issue["code"] == "line_paragraph_mismatch")
    assert issue["language"] == "fa"
    row = next(row for row in result["stages"] if row["stage"] == "a1")
    assert row["eligible_authored_stories"] == 0
    assert row["authored_story_shortfall"] == 200


def test_missing_english_line_is_not_a_complete_translation(tmp_path):
    value = story()
    del value["lines"][2]["en"]
    write_pack(tmp_path, "a1", [value])
    assert "missing_story_translation" in codes(MODULE.audit(tmp_path))


def test_identical_cross_stage_text_does_not_become_new_content(tmp_path):
    first = story()
    second = deepcopy(first)
    second["id"] = "b1-new-name"
    second["title"]["nl"] = "Een andere titel"
    write_pack(tmp_path, "a1", [first])
    write_pack(tmp_path, "b1", [second])
    result = MODULE.audit(tmp_path)
    assert "exact_story_duplicate" in codes(result)
    row = next(row for row in result["stages"] if row["stage"] == "b1")
    assert row["eligible_authored_stories"] == 0


def test_appending_a_moral_does_not_hide_a_near_copy(tmp_path):
    first = story()
    second = deepcopy(first)
    second["id"] = "a2-tail"
    second["lines"][-1]["nl"] += " Daarom is goede communicatie heel belangrijk."
    second["paragraphs"][-1]["nl"] += " Daarom is goede communicatie heel belangrijk."
    write_pack(tmp_path, "a1", [first])
    write_pack(tmp_path, "a2", [second])
    result = MODULE.audit(tmp_path)
    assert "near_copy_needs_review" in codes(result)
    assert next(row for row in result["stages"] if row["stage"] == "a2")["eligible_authored_stories"] == 0


def test_repeated_short_expression_is_not_automatically_a_repeated_plot(tmp_path):
    first = story()
    first["lines"] = [{lang: "Goedemorgen!" for lang in MODULE.LANGS}] * 8
    first["paragraphs"] = [{lang: " ".join(["Goedemorgen!"] * 4) for lang in MODULE.LANGS}] * 2
    other = story("a2-other", "Daarna ")
    other["lines"][0]["nl"] = "Goedemorgen!"
    other["paragraphs"][0]["nl"] = " ".join(line["nl"] for line in other["lines"][:4])
    write_pack(tmp_path, "a1", [first])
    write_pack(tmp_path, "a2", [other])
    assert "near_copy_needs_review" not in codes(MODULE.audit(tmp_path))


def test_numeric_screen_normalizes_persian_digits_and_flags_changed_fact(tmp_path):
    value = story()
    value["lines"][0] = {"nl": "De tas kost 12 euro.", "en": "The bag costs 21 euros.",
                           "fa": "کیف ۱۲ یورو قیمت دارد."}
    for lang in MODULE.LANGS:
        value["paragraphs"][0][lang] = " ".join(line[lang] for line in value["lines"][:4])
    write_pack(tmp_path, "a1", [value])
    assert "numeric_translation_review" in codes(MODULE.audit(tmp_path))
    assert MODULE.quantities("۱۴:۰۰") == MODULE.quantities("14.00")
    assert MODULE.quantities("2026-10-05") == MODULE.quantities("05/10/2026") == set()


def test_structural_success_never_claims_level_or_language_approval(tmp_path):
    write_pack(tmp_path, "a1", [story()])
    result = MODULE.audit(tmp_path, minimum_stories=0, minimum_words=0)
    assert result["inventory_status"] == "target_count_met_needs_editorial_review"
    assert "CEFR" in result["claim"]
    assert result["structural_errors"] == 0
