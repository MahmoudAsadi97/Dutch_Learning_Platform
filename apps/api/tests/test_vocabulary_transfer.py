"""Authored context packs stay stage-bound and cannot alter learner evidence."""
from __future__ import annotations

import importlib.util
import json
import shutil
from copy import deepcopy

import pytest
from pydantic import ValidationError

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import library, word_usage
from dlp.domains.curriculum.schemas import STAGE_IDS


def source_data(stage="pre-a1"):
    return json.loads((CONTENT_DIR / "library" / f"{stage}.json").read_text(encoding="utf-8"))


def pack_data(stage="pre-a1"):
    return json.loads((CONTENT_DIR / "vocabulary-transfer" / f"{stage}.json").read_text(encoding="utf-8"))


def write_pack(root, data):
    directory = root / "vocabulary-transfer"
    directory.mkdir(exist_ok=True)
    path = directory / f"{data['stage_id']}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("stage", STAGE_IDS)
def test_every_stage_has_original_transfer_examples_without_replacing_its_word_bank(stage):
    original = source_data(stage)
    enriched = word_usage.enrich(original, CONTENT_DIR)
    assert [word["id"] for word in enriched["vocabulary"]] == [word["id"] for word in original["vocabulary"]]
    assert len(enriched["vocabulary"]) >= 500
    changed = [word for word in enriched["vocabulary"] if word.get("contexts")]
    assert len(changed) >= 3
    for word in changed:
        parsed = library.LibraryWord.model_validate(word)
        assert len(parsed.contexts) >= 3
        assert len({context.setting.nl for context in parsed.contexts}) >= 2
        assert len({context.sentence.nl for context in parsed.contexts}) == len(parsed.contexts)
        assert all(context.production_prompt.nl and context.production_prompt.en and context.production_prompt.fa
                   for context in parsed.contexts)
    # The overlay is pure: serving an example does not rewrite source words or generate credit.
    assert original == source_data(stage)
    assert not any(key in enriched for key in ("mastered", "score", "completed", "learned"))


def test_noun_forms_are_explicit_and_verb_forms_are_complete_localized_examples():
    beginner = word_usage.enrich(source_data(), CONTENT_DIR)
    name = next(word for word in beginner["vocabulary"] if word["term"] == "de naam")
    assert name["article"] == "de" and name["plural"] == "namen"
    assert all(context["structure"] in {"present", "adjective", "noun_phrase"}
               for word in beginner["vocabulary"] for context in word.get("contexts", []))
    intermediate = word_usage.enrich(source_data("a2"), CONTENT_DIR)
    verb = next(word for word in intermediate["vocabulary"] if word["term"] == "terugbellen")
    assert verb["article"] is None and verb["plural"] is None
    assert {context["structure"] for context in verb["contexts"]} == {"past", "future", "modal"}
    assert any(form["text"]["nl"] == "Ik heb je teruggebeld, maar je nam niet op." for form in verb["forms"])
    assert all(set(form["text"]) == {"nl", "en", "fa"} for form in verb["forms"])


@pytest.mark.parametrize("case", ["foreign-word", "wrong-term", "duplicate-word", "duplicate-context-id",
                                  "duplicate-context-text", "unsupported-field", "blank-persian", "one-context",
                                  "too-advanced", "invented-review"])
def test_invalid_pack_cannot_silently_supply_unrelated_or_premature_content(tmp_path, case):
    data = pack_data()
    first = data["entries"][0]
    if case == "foreign-word":
        first["word_id"] = "c2-v001"
    elif case == "wrong-term":
        first["term"] = "de verkeerde betekenis"
    elif case == "duplicate-word":
        data["entries"].append(deepcopy(first))
    elif case == "duplicate-context-id":
        first["contexts"][1]["id"] = first["contexts"][0]["id"]
    elif case == "duplicate-context-text":
        first["contexts"][1]["sentence"] = deepcopy(first["contexts"][0]["sentence"])
    elif case == "unsupported-field":
        first["mastered"] = True
    elif case == "blank-persian":
        first["contexts"][0]["sentence"]["fa"] = "   "
    elif case == "one-context":
        first["contexts"] = first["contexts"][:1]
    elif case == "too-advanced":
        first["contexts"][0]["structure"] = "conditional"
    elif case == "invented-review":
        data["review_status"] = "approved"
    write_pack(tmp_path, data)
    with pytest.raises((ValueError, ValidationError)):
        word_usage.enrich(source_data(), tmp_path)


def test_context_cannot_claim_another_words_id(tmp_path):
    data = pack_data()
    data["entries"][0]["contexts"][0]["id"] = "pre-a1-v999-use-1"
    write_pack(tmp_path, data)
    with pytest.raises(ValueError, match="belong to their word"):
        word_usage.enrich(source_data(), tmp_path)


def test_noun_metadata_cannot_be_applied_to_a_verb():
    word = source_data()["vocabulary"][0]
    with pytest.raises(ValidationError, match="only a noun"):
        library.LibraryWord.model_validate({**word, "part_of_speech": "verb", "article": "de"})


def test_missing_overlay_preserves_legacy_data_and_stage_path_is_validated(tmp_path):
    data = source_data()
    assert word_usage.enrich(data, tmp_path) == data
    for stage in ("../private", "a3", "PRE-A1", "a1/../../secret"):
        with pytest.raises(ValueError, match="unknown stage"):
            word_usage.stamp(tmp_path, stage)


def test_pack_cache_does_not_return_a_mutable_result_to_the_next_request(tmp_path):
    data = pack_data()
    write_pack(tmp_path, data)
    first = word_usage.enrich(source_data(), tmp_path)
    word = next(item for item in first["vocabulary"] if item.get("contexts"))
    word["contexts"][0]["sentence"]["nl"] = "Changed by caller"
    second = word_usage.enrich(source_data(), tmp_path)
    word = next(item for item in second["vocabulary"] if item.get("contexts"))
    assert word["contexts"][0]["sentence"]["nl"] != "Changed by caller"


def test_published_library_and_its_story_words_expose_the_same_authored_contexts():
    bank = library.library_for("pre-a1")
    word = next(item for item in bank.vocabulary if item.term == "de naam")
    page = library.vocabulary_page(bank, query="de naam")
    item = next(item for item in page["items"] if item["id"] == word.id)
    assert len(item["contexts"]) == 3
    story = next(story for story in bank.stories if word.id in story.vocabulary_ids)
    linked = next(item for item in library.story_detail(bank, story.id)["vocabulary"] if item["id"] == word.id)
    assert linked["contexts"] == item["contexts"]


def test_authored_pack_builder_reproduces_published_bytes_without_mutating_source_words(tmp_path):
    source = CONTENT_DIR.parent / "scripts/content_build/vocabulary_transfer.py"
    spec = importlib.util.spec_from_file_location("vocabulary_transfer_builder", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory = tmp_path / "content/library"
    directory.mkdir(parents=True)
    for stage in STAGE_IDS:
        shutil.copyfile(CONTENT_DIR / "library" / f"{stage}.json", directory / f"{stage}.json")
    result = module.build(tmp_path)
    assert set(result) == set(STAGE_IDS)
    for stage in STAGE_IDS:
        assert (tmp_path / "content/vocabulary-transfer" / f"{stage}.json").read_bytes() == (
            CONTENT_DIR / "vocabulary-transfer" / f"{stage}.json").read_bytes()
        assert (directory / f"{stage}.json").read_bytes() == (CONTENT_DIR / "library" / f"{stage}.json").read_bytes()
