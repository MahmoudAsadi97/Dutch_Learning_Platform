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


def guided_lesson(identifier="a1-guided-reading", source_id=None):
    value = story(identifier)
    value.pop("paragraphs")
    value["lines"] = [{key: line[key] for key in ("nl", "en")} for line in value["lines"]]
    value["title"]["en"] = "A book in the park"
    value["topic_id"] = "books-reading"
    if source_id:
        value["source_id"] = source_id
    return value


def write_guided(root, stage, lessons):
    path = root / "study/packs" / f"{stage}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "stage_id": stage, "review_status": "unreviewed",
                                "lessons": lessons}, ensure_ascii=False))


def write_reading(root, stage, lessons, name="01-books"):
    for lesson in lessons:
        lesson["id"] = lesson["id"].replace("-reading-", "-read-")
        first = lesson["lines"][0]
        lesson.setdefault("words", [
            {"term": term, "part_of_speech": kind, "meaning": {"nl": nl, "en": en},
             "example": first, "minimum_stage": stage}
            for term, kind, nl, en in (
                ("het boek", "noun", "Een tekst met bladzijden.", "A book."),
                ("meenemen", "verb", "Iets naar een andere plek brengen.", "To take along."),
                ("het park", "noun", "Een groene plek om te wandelen.", "A park."))])
        lesson.setdefault("grammar", [{
            "title": {"nl": "Een scheidbaar werkwoord", "en": "A separable verb"},
            "explanation": {"nl": "Neemt en mee zijn de twee delen van meenemen.",
                            "en": "Neemt and mee are the two parts of meenemen."},
            "examples": [first]}])
        lesson.setdefault("questions", [{
            "id": f"q{number}", "prompt": {"nl": "Wat neemt Sara mee?", "en": "What does Sara take?"},
            "options": [{"nl": "Een boek", "en": "A book"}, {"nl": "Een tas", "en": "A bag"}],
            "answer_index": 0, "explanation": first} for number in (1, 2)])
    path = root / "study/reading" / stage / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "stage_id": stage, "language_variety": "nl-BE",
                                "review_status": "unreviewed", "lessons": lessons}, ensure_ascii=False))
    return path


def stage_row(result, stage="a1"):
    return next(row for row in result["stages"] if row["stage"] == stage)


def test_guided_alias_selects_resolvable_representation_without_inflating_work_count(tmp_path):
    original = story()
    write_pack(tmp_path, "a1", [original])
    write_guided(tmp_path, "a1", [guided_lesson(source_id=original["id"])])
    result = MODULE.audit(tmp_path)
    row = stage_row(result)
    assert row["authored_stories"] == row["eligible_authored_stories"] == 1
    assert row["legacy_library_authored_stories"] == row["legacy_library_eligible_stories"] == 1
    record, = result["canonical_stories"]
    assert record["canonical_id"] == original["id"]
    assert record["source_kind"] == "guided"
    assert record["lesson_id"] == "a1-guided-reading"
    assert record["source_id"] == "a1-guided-reading"
    assert record["aliases"] == ["a1-guided-reading", original["id"]]
    assert "exact_story_duplicate" not in codes(result)


def test_expanded_short_source_counts_once_and_does_not_relabel_the_old_bank(tmp_path):
    original = story()
    original.pop("lines")
    write_pack(tmp_path, "a1", [original])
    lesson = guided_lesson(source_id=original["id"])
    lesson["lines"][-1]["nl"] += " Sara leest thuis verder."
    write_guided(tmp_path, "a1", [lesson])
    row = stage_row(MODULE.audit(tmp_path))
    assert row["legacy_stories"] == 1
    assert row["legacy_library_authored_stories"] == row["legacy_library_eligible_stories"] == 0
    assert row["eligible_authored_stories"] == 1


def test_reading_batches_need_no_invented_persian_translation(tmp_path):
    lesson = guided_lesson("a1-reading-letter")
    lesson["plot_key"] = "A child follows eight numbered clues to find a book."
    write_reading(tmp_path, "a1", [lesson])
    result = MODULE.audit(tmp_path)
    record, = MODULE.canonical_story_records(tmp_path, "a1")
    assert record["eligible"] is True
    assert record["path"] == "study/reading/a1/01-books.json"
    assert record["canonical_id"] == lesson["id"]
    assert record["source_kind"] == "reading"
    assert all(set(line) == {"nl", "en"} for line in record["lines"])
    assert stage_row(result)["eligible_authored_stories"] == 1
    assert stage_row(result)["legacy_library_stories_total"] == 0
    assert "missing_story_translation" not in codes(result)


def test_reading_batch_missing_english_is_ineligible(tmp_path):
    lesson = guided_lesson("a1-reading-letter")
    lesson["plot_key"] = "A child follows eight numbered clues to find a book."
    del lesson["lines"][3]["en"]
    write_reading(tmp_path, "a1", [lesson])
    result = MODULE.audit(tmp_path)
    assert stage_row(result)["eligible_authored_stories"] == 0
    assert result["canonical_structural_errors"] > 0


def test_repeating_a_line_cannot_pad_a_new_story(tmp_path):
    lesson = guided_lesson("a1-reading-letter")
    lesson["plot_key"] = "A child follows eight numbered clues to find a book."
    lesson["lines"][-1] = deepcopy(lesson["lines"][0])
    write_reading(tmp_path, "a1", [lesson])
    result = MODULE.audit(tmp_path)
    assert "repeated_story_line" in codes(result)
    assert stage_row(result)["eligible_authored_stories"] == 0


def test_shared_screen_catches_a_copy_between_guided_and_reading_sources(tmp_path):
    write_guided(tmp_path, "a1", [guided_lesson()])
    lesson = guided_lesson("a2-reading-letter")
    lesson["plot_key"] = "A different title is not a different story."
    lesson["lines"][-1]["nl"] += " Dat was een goed idee."
    write_reading(tmp_path, "a2", [lesson])
    result = MODULE.audit(tmp_path)
    assert "near_copy_needs_review" in codes(result)
    assert stage_row(result, "a2")["eligible_authored_stories"] == 0


def test_guided_expansion_does_not_hide_a_cross_stage_copy_under_an_alias(tmp_path):
    original = story("a1-short")
    original.pop("lines")
    write_pack(tmp_path, "a1", [original])
    other = deepcopy(original)
    other["id"] = "a2-short"
    write_pack(tmp_path, "a2", [other])
    lesson = guided_lesson("a2-expanded", source_id="a2-short")
    lesson["lines"][-1]["nl"] += " Dat was een goed idee."
    write_guided(tmp_path, "a2", [lesson])
    result = MODULE.audit(tmp_path)
    assert any(issue["code"] == "near_copy_needs_review" and issue["story_id"] == "a2-expanded"
               for issue in result["issues"])
    assert stage_row(result, "a2")["eligible_authored_stories"] == 0


def test_distinct_wording_with_same_declared_plot_needs_review_not_a_second_count(tmp_path):
    first = guided_lesson("a1-reading-letter")
    first["plot_key"] = "A reader follows numbered clues to a missing book."
    second = guided_lesson("a2-reading-letter")
    second["plot_key"] = first["plot_key"]
    second["lines"] = [{"nl": f"Dinsdag verzorgt Amir plant {i} in de serre.",
                        "en": f"On Tuesday Amir tends plant {i} in the greenhouse."} for i in range(1, 9)]
    write_reading(tmp_path, "a1", [first])
    write_reading(tmp_path, "a2", [second])
    result = MODULE.audit(tmp_path)
    assert "repeated_plot_synopsis" in codes(result)
    assert stage_row(result, "a2")["eligible_authored_stories"] == 0


def test_old_short_bank_errors_remain_visible_but_are_not_canonical_draft_errors(tmp_path):
    first = story()
    first.pop("lines")
    second = deepcopy(first)
    second["id"] = "b1-old-copy"
    write_pack(tmp_path, "a1", [first])
    write_pack(tmp_path, "b1", [second])
    result = MODULE.audit(tmp_path)
    assert result["structural_errors"] > 0
    assert result["canonical_structural_errors"] == 0
    assert "exact_story_duplicate" in codes(result)
    assert not result["canonical_stories"]


def test_reading_batch_cannot_claim_editorial_approval(tmp_path):
    lesson = guided_lesson("a1-reading-letter")
    lesson["plot_key"] = "A child follows eight numbered clues to find a book."
    path = write_reading(tmp_path, "a1", [lesson])
    data = json.loads(path.read_text())
    data["review_status"] = "approved"
    path.write_text(json.dumps(data))
    result = MODULE.audit(tmp_path)
    assert "invalid_reading_batch" in codes(result)
    assert result["canonical_structural_errors"] > 0
    assert stage_row(result)["eligible_authored_stories"] == 0


@pytest.mark.parametrize("fault", ["missing_words", "unrelated_grammar", "missing_questions"])
def test_inventory_cannot_count_a_reading_the_runtime_would_reject(tmp_path, fault):
    lesson = guided_lesson("a1-read-incomplete")
    lesson["plot_key"] = "A child follows eight numbered clues to find a book."
    path = write_reading(tmp_path, "a1", [lesson])
    document = json.loads(path.read_text())
    authored = document["lessons"][0]
    if fault == "missing_words":
        authored["words"] = []
    elif fault == "unrelated_grammar":
        authored["grammar"][0]["examples"] = [{"nl": "De trein vertrekt.", "en": "The train leaves."}]
    else:
        authored["questions"] = []
    path.write_text(json.dumps(document))
    result = MODULE.audit(tmp_path)
    assert "invalid_reading_batch" in codes(result)
    assert stage_row(result)["eligible_authored_stories"] == 0


def test_decimal_and_clock_punctuation_does_not_create_a_translation_error():
    assert MODULE.quantities("12,50 euro") == MODULE.quantities("12.50 euros") == MODULE.quantities("۱۲٫۵۰ یورو")
    assert MODULE.quantities("om 14.00 uur") == MODULE.quantities("at 14:00") == MODULE.quantities("ساعت ۱۴:۰۰")
    assert MODULE.quantities("12,50 euro") != MODULE.quantities("21.50 euros")


def test_only_changing_names_places_and_numbers_does_not_create_a_distinct_story(tmp_path):
    first = guided_lesson("a1-reading-sara")
    first["plot_key"] = "A reader follows clues to find a book."
    second = deepcopy(first)
    second["id"] = "a2-reading-amir"
    second["plot_key"] = "A new name does not change the plot."
    for line in second["lines"]:
        line["nl"] = line["nl"].replace("Sara", "Amir").replace("1", "9")
    write_reading(tmp_path, "a1", [first])
    write_reading(tmp_path, "a2", [second])
    result = MODULE.audit(tmp_path)
    assert "surface_variant_needs_review" in codes(result)
    assert stage_row(result, "a2")["eligible_authored_stories"] == 0
