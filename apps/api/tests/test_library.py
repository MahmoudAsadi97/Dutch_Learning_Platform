"""Counts, references, pagination and identity boundaries for the published learning libraries."""
from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from dlp.domains.curriculum import library
from dlp.domains.curriculum.library import StageLibrary
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.curriculum.service import CurriculumError


def localized(text):
    return {"nl": text, "en": f"English {text}", "fa": f"فارسی {text}"}


@pytest.fixture
def bank_data():
    words = [{"id": f"word-{i}", "term": f"woord{i}", "topic": localized("Eten" if i < 250 else "Werk"),
              "meaning": localized(f"betekenis{i}"), "example": localized(f"Hier staat woord{i}.")}
             for i in range(500)]
    stories = [{
        "id": f"story-{i}", "title": localized(f"Verhaal {i}"), "topic": localized("Eten" if i < 50 else "Werk"),
        "paragraphs": [localized(f"In verhaal {i} gebeurt iets."), localized(f"Daarna eindigt verhaal {i}.")],
        "vocabulary_ids": [f"word-{j}" for j in range(i * 5, i * 5 + 5)],
        "question": {"prompt": localized("Wat gebeurt er?"), "options": [localized("Dit"), localized("Dat")],
                     "answer_index": 0, "explanation": localized("Lees de eerste alinea.")},
    } for i in range(100)]
    return {"schema_version": 1, "stage_id": "pre-a1", "review_status": "unreviewed",
            "vocabulary": words, "stories": stories}


@pytest.fixture
def bank(bank_data):
    return StageLibrary.model_validate(bank_data)


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_published_stage_has_500_unique_words_and_100_distinct_two_paragraph_stories(stage_id):
    # Deliberately do not skip absent files: an incomplete content upload must fail CI/release.
    bank = library.library_for(stage_id)
    assert bank.stage_id == stage_id and bank.review_status == "unreviewed"
    assert len(bank.vocabulary) >= 500 and len(bank.stories) >= 100
    assert len({library.normalise(word.term) for word in bank.vocabulary}) == len(bank.vocabulary)
    assert all(len(story.paragraphs) >= 2 for story in bank.stories)
    assert {word.id for word in bank.vocabulary} == {key for story in bank.stories for key in story.vocabulary_ids}
    assert len({library.normalise(" ".join(part.nl for part in story.paragraphs)) for story in bank.stories}) == len(bank.stories)


def test_minimum_counts_and_paragraph_count_cannot_be_filled_by_schema_defaults(bank_data):
    for mutate in (
        lambda data: data["vocabulary"].pop(),
        lambda data: data["stories"].pop(),
        lambda data: data["stories"][0]["paragraphs"].pop(),
    ):
        data = deepcopy(bank_data)
        mutate(data)
        with pytest.raises(ValidationError):
            StageLibrary.model_validate(data)


@pytest.mark.parametrize("case", ["word-id", "word-term", "story-id", "story-text", "blank-term",
                                  "blank-translation", "invalid-answer", "unknown-ref", "repeated-ref", "uncovered-word",
                                  "unknown-stage", "invented-review"])
def test_duplicate_missing_or_unreviewed_content_constraints_are_enforced(bank_data, case):
    words, stories = bank_data["vocabulary"], bank_data["stories"]
    if case == "word-id":
        words[1]["id"] = words[0]["id"]
    elif case == "word-term":
        words[1]["term"] = f"  {words[0]['term'].upper()}  "
    elif case == "story-id":
        stories[1]["id"] = stories[0]["id"]
    elif case == "story-text":
        stories[1]["paragraphs"] = deepcopy(stories[0]["paragraphs"])
    elif case == "blank-term":
        words[0]["term"] = "  "
    elif case == "blank-translation":
        stories[0]["paragraphs"][0]["fa"] = "  "
    elif case == "invalid-answer":
        stories[0]["question"]["answer_index"] = 2
    elif case == "unknown-ref":
        stories[0]["vocabulary_ids"][0] = "unknown"
    elif case == "repeated-ref":
        stories[0]["vocabulary_ids"].append(stories[0]["vocabulary_ids"][0])
    elif case == "uncovered-word":
        stories[0]["vocabulary_ids"].pop()
    elif case == "unknown-stage":
        bank_data["stage_id"] = "a3"
    elif case == "invented-review":
        bank_data["review_status"] = "approved"
    with pytest.raises(ValidationError):
        StageLibrary.model_validate(bank_data)


def test_normalisation_handles_case_space_and_unicode_equivalents():
    assert library.normalise("  CAFÉ  ") == library.normalise("cafe\u0301")
    assert library.normalise("de\u00a0  bus") == "de bus"


@pytest.mark.parametrize("stage_id", ["../private", "..", "a3", "../../.env", "a1/../c2", "%2e%2e", "/a1", "A1"])
def test_stage_lookup_rejects_invalid_paths_before_touching_files(tmp_path, monkeypatch, stage_id):
    monkeypatch.setattr(library, "CONTENT_DIR", tmp_path)
    with pytest.raises(CurriculumError) as error:
        library.library_for(stage_id)
    assert error.value.status_code == 404


def test_library_filename_is_bound_to_requested_stage(bank, tmp_path, monkeypatch):
    (tmp_path / "library").mkdir()
    (tmp_path / "library/a1.json").write_text(bank.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(library, "CONTENT_DIR", tmp_path)
    with pytest.raises(ValueError, match="does not match"):
        library.library_for("a1")


def test_bounded_pages_have_no_duplicate_rows_and_summary_counts_are_consistent(bank):
    first = library.vocabulary_page(bank, offset=0, limit=20)
    second = library.vocabulary_page(bank, offset=20, limit=20)
    assert len(first["items"]) == len(second["items"]) == 20
    assert first["total"] == second["total"] == 500
    assert not {word["id"] for word in first["items"]} & {word["id"] for word in second["items"]}
    assert library.vocabulary_page(bank, offset=500)["items"] == []
    stories = library.story_page(bank, offset=96, limit=12)
    assert stories["total"] == 100 and len(stories["items"]) == 4
    assert "paragraphs" not in stories["items"][0] and "question" not in stories["items"][0]
    summary = library.summary(bank)
    assert summary["vocabulary_count"] == sum(topic["vocabulary_count"] for topic in summary["topics"]) == 500
    assert summary["story_count"] == sum(topic["story_count"] for topic in summary["topics"]) == 100


def test_search_is_literal_multilingual_and_topic_scoped(bank):
    assert library.vocabulary_page(bank, topic="Eten")["total"] == 250
    assert library.vocabulary_page(bank, topic="Made up")["total"] == 0
    assert library.vocabulary_page(bank, query="WOORD499", topic="Werk")["total"] == 1
    assert library.vocabulary_page(bank, query="فارسی betekenis499")["total"] == 1
    assert library.vocabulary_page(bank, query=".*")["total"] == 0
    assert library.story_page(bank, query="English In verhaal 99")["total"] == 1
    assert library.story_page(bank, query="فارسی In verhaal 99")["total"] == 1
    assert library.story_page(bank, query="%'; DROP TABLE learners;--")["total"] == 0


def test_story_detail_contains_only_its_referenced_words_and_practice_question(bank):
    item = library.story_detail(bank, "story-0")
    assert {word["id"] for word in item["vocabulary"]} == set(item["vocabulary_ids"])
    assert len(item["vocabulary"]) == 5
    assert item["question"]["id"] == "story-0-understand"
    assert item["question"]["answer_index"] == 0  # guided practice, not a final-test answer
    with pytest.raises(CurriculumError) as error:
        library.story_detail(bank, "../.env")
    assert error.value.status_code == 404


def test_story_id_cannot_validate_then_break_the_derived_practice_question(bank_data):
    bank_data["stories"][0]["id"] = "s" * 69
    bank = StageLibrary.model_validate(bank_data)
    assert len(library.story_detail(bank, "s" * 69)["question"]["id"]) == 80
    bank_data["stories"][0]["id"] = "s" * 70
    with pytest.raises(ValidationError):
        StageLibrary.model_validate(bank_data)


def test_library_api_auth_pagination_search_and_unknown_ids(client, headers, bank, monkeypatch):
    real_lookup = library.library_for
    def lookup(stage_id):
        if stage_id == "pre-a1":
            return bank
        return real_lookup(stage_id)
    monkeypatch.setattr(library, "library_for", lookup)
    for suffix in ("", "/vocabulary", "/stories", "/stories/story-0"):
        assert client.get(f"/library/pre-a1{suffix}").status_code == 401
        assert client.get(f"/library/pre-a1{suffix}", headers=headers).status_code == 200
    for path in ("/library/a3", "/library/not-real/vocabulary", "/library/pre-a1/stories/not-real",
                 "/library/%2E%2E%2F.env/vocabulary", "/library/pre-a1/stories/%2E%2E%2F.env"):
        assert client.get(path, headers=headers).status_code == 404
    for query in ("offset=-1", "offset=100001", "limit=0", "limit=51", "limit=abc", "q=" + "x" * 121,
                  "topic=" + "x" * 161):
        assert client.get(f"/library/pre-a1/vocabulary?{query}", headers=headers).status_code == 422
    assert client.get("/library/pre-a1/stories?limit=31", headers=headers).status_code == 422
    assert client.get("/library/pre-a1/vocabulary?offset=100000", headers=headers).json()["items"] == []
    search = client.get("/library/pre-a1/vocabulary", headers=headers, params={"q": "WOORD499", "topic": "Werk"})
    assert search.json()["total"] == 1 and len(search.json()["items"]) == 1
    assert "learner_key" in client.get("/library/pre-a1", headers=headers).json()
