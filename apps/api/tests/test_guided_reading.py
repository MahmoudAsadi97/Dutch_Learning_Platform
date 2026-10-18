"""Original readings retain their source, level and transient practice contract."""
from __future__ import annotations

import importlib.util
import json
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from dlp.config import Settings
from dlp.domains.curriculum import story_inventory
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.study import content, feedback
from dlp.domains.study.reading_sources import read_reading_batches
from dlp.domains.study.responses import StudyLesson
from dlp.domains.study.schemas import FeedbackBody, IndexDocument, ReadingDocument, TopicDocument
from dlp.providers.fixtures import FixtureChatModel

SPEC = importlib.util.spec_from_file_location(
    "guided_reading_audit", Path(__file__).resolve().parents[3] / "scripts/audit_guided_study.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def reading(stage="pre-a1", slug="sister-name"):
    pairs = [
        ("Dag, ik ben Noor.", "Hello, I am Noor."),
        ("Dit is mijn zus.", "This is my sister."),
        ("Zij heet Sara.", "Her name is Sara."),
        ("Sara is hier.", "Sara is here."),
        ("Dit is mijn mama.", "This is my mum."),
        ("Mama zegt: dag, Sara!", "Mum says: hello, Sara!"),
        ("Sara zegt: dag, mama!", "Sara says: hello, Mum!"),
        ("Wij zijn thuis.", "We are at home."),
    ]
    lines = [{"nl": nl, "en": en} for nl, en in pairs]
    words = [("de zus", "noun", "Een meisje of vrouw met dezelfde ouders.", "A sister.", 1),
             ("heten", "verb", "Een naam hebben.", "To have a name.", 2),
             ("thuis", "adverb", "Op de plek waar je woont.", "At home.", 7)]
    return {"id": f"{stage}-read-{slug}", "topic_id": "family",
            "title": {"nl": "De naam van mijn zus", "en": "My sister's name"},
            "plot_key": "Noor introduces her sister Sara to her mother and both greet one another at home.",
            "lines": lines,
            "words": [{"term": term, "part_of_speech": kind, "meaning": {"nl": nl, "en": en},
                       "example": lines[index], "minimum_stage": stage} for term, kind, nl, en, index in words],
            "grammar": [{"title": {"nl": "Een naam zeggen", "en": "Saying a name"},
                         "explanation": {"nl": "Met heet zeg je de naam van iemand.",
                                         "en": "Use heet to say someone's name."}, "examples": [lines[2]]}],
            "questions": [
                {"id": "sister-name", "prompt": {"nl": "Hoe heet de zus?", "en": "What is the sister's name?"},
                 "options": [{"nl": "Sara", "en": "Sara"}, {"nl": "Noor", "en": "Noor"}],
                 "answer_index": 0, "explanation": lines[2]},
                {"id": "family-place", "prompt": {"nl": "Waar zijn zij?", "en": "Where are they?"},
                 "options": [{"nl": "Thuis", "en": "At home"}, {"nl": "Op school", "en": "At school"}],
                 "answer_index": 0, "explanation": lines[-1]}]}


def write_reading(root, lesson, batch="01"):
    stage = lesson["id"].split("-read-", 1)[0]
    path = root / "study" / "reading" / stage / f"{batch}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": 1, "stage_id": stage, "language_variety": "nl-BE",
                "review_status": "unreviewed", "lessons": [lesson]}
    path.write_text(json.dumps(document), encoding="utf-8")
    return path, document


def install_reading(monkeypatch, tmp_path, lesson=None):
    lesson = lesson or reading()
    stage = lesson["id"].split("-read-", 1)[0]
    write_reading(tmp_path, lesson)
    topics = TopicDocument.model_validate_json((content.CONTENT_DIR / "study/topics.json").read_text())
    index = IndexDocument(schema_version=1, stages={stage: {
        skill: {lesson["topic_id"]: [{"source": "reading", "id": lesson["id"]}]} if skill == "reading" else {}
        for skill in SKILLS}})
    monkeypatch.setattr(content, "CONTENT_DIR", tmp_path)
    monkeypatch.setattr(content, "documents", lambda: (topics, index))
    monkeypatch.setattr(content, "pack_for", lambda stage: None)
    return lesson


@pytest.mark.parametrize("change", ["wrong_id", "missing_words", "foreign_stage", "unrelated_example",
                                    "missing_grammar", "relabelled_source", "other_skill", "foreign_translation"])
def test_reading_batch_rejects_invalid_identity_or_preparation(tmp_path, change):
    lesson = reading()
    _, document = write_reading(tmp_path, lesson)
    if change == "wrong_id":
        lesson["id"] = "a1-read-other"
    elif change == "missing_words":
        lesson["words"] = lesson["words"][:2]
    elif change == "foreign_stage":
        lesson["words"][0]["minimum_stage"] = "c2"
    elif change == "unrelated_example":
        lesson["words"][0]["example"] = {"nl": "Ik ga naar school.", "en": "I go to school."}
    elif change == "missing_grammar":
        lesson["grammar"] = []
    elif change == "relabelled_source":
        lesson["source_id"] = "pre-a1-old-story"
    elif change == "other_skill":
        lesson["speaking"] = {"short_questions": []}
    else:
        lesson["lines"][0]["fa"] = "een verborgen vertaling"
    with pytest.raises(ValidationError):
        ReadingDocument.model_validate(document)


def test_batch_loading_retains_stage_and_refuses_duplicates_across_files(monkeypatch, tmp_path):
    lesson = reading()
    write_reading(tmp_path, lesson)
    monkeypatch.setattr(content, "CONTENT_DIR", tmp_path)
    assert content.readings_for("pre-a1")[0].id == lesson["id"]
    other = deepcopy(lesson)
    other["id"] = "pre-a1-read-renamed-copy"
    write_reading(tmp_path, other, "02")
    with pytest.raises(ValueError, match="identity or plot"):
        content.readings_for("pre-a1")
    path, document = write_reading(tmp_path, reading(), "03")
    document["stage_id"] = "c2"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="directory"):
        list(read_reading_batches(tmp_path))


def test_reading_sources_cannot_leak_into_another_skill():
    with pytest.raises(ValidationError, match="only to the reading"):
        IndexDocument(schema_version=1, stages={"pre-a1": {
            "speaking": {"family": [{"source": "reading", "id": "pre-a1-read-sister-name"}]}}})


def test_exact_reading_renders_without_loading_legacy_banks_and_hides_keys(monkeypatch, tmp_path):
    source = install_reading(monkeypatch, tmp_path)

    def legacy_not_needed(*args):
        raise AssertionError("an authored reading must not load a complete legacy bank")

    monkeypatch.setattr(content, "library_for", legacy_not_needed)
    result = content.lesson("pre-a1", "family", "reading", activity_id=source["id"])
    assert result["activity_id"] == source["id"]
    assert result["title"] == source["title"]
    assert result["parts"][0]["text"] == source["lines"]
    assert len(result["preparation"]["words"]) == 3
    assert result["preparation"]["grammar"] == source["grammar"]
    assert result["policy"]["ephemeral"] is True
    assert result["policy"]["pronunciation_assessed"] is False
    StudyLesson.model_validate({**result, "policy": {**result["policy"], "recording_max_seconds": 60}})
    assert '"answer_index"' not in json.dumps(result)
    assert '"fa"' not in json.dumps(result)
    with pytest.raises(CurriculumError):
        content.lesson("pre-a1", "family", "reading", activity_id="pre-a1-read-missing")
    with pytest.raises(CurriculumError):
        content.lesson("pre-a1", "family", "speaking", activity_id=source["id"])


def test_reading_cannot_be_relabelled_by_editing_its_index(monkeypatch, tmp_path):
    source = install_reading(monkeypatch, tmp_path)
    topics, index = content.documents()
    mapped = index.model_copy(deep=True)
    mapped.stages["pre-a1"]["reading"]["friends"] = mapped.stages["pre-a1"]["reading"].pop("family")
    monkeypatch.setattr(content, "documents", lambda: (topics, mapped))
    with pytest.raises(ValueError, match="authored topic"):
        content.lesson("pre-a1", "friends", "reading", activity_id=source["id"])


def test_reading_feedback_uses_original_keys_without_any_learning_database(monkeypatch, tmp_path):
    source = install_reading(monkeypatch, tmp_path)
    result = feedback.evaluate(None, Settings(_env_file=None), FixtureChatModel(),
                               learner_id=uuid.uuid4(), stage_id="pre-a1", topic_id="family",
                               body=FeedbackBody(skill="reading", activity_id=source["id"], part="read",
                                                 kind="answers", answers={"sister-name": 0, "family-place": 0}),
                               request_id="reading-check-0001")
    assert result["score"] == 10
    assert result["ephemeral"] is True
    assert result["dimensions"]["pronunciation"] is None


def test_retelling_demand_grows_with_the_learning_stage():
    lines = reading()["lines"]
    beginning = content._reading_parts("pre-a1", lines, [])[1]
    advanced = content._reading_parts("c2", lines, [])[1]
    assert beginning["max_words"] < advanced["max_words"]
    assert beginning["min_words"] == 1
    assert "one short sentence" in beginning["prompt"]["en"]
    assert "infer" in advanced["prompt"]["en"]


def test_index_uses_explicit_original_mapping_and_suppresses_an_adapted_source(monkeypatch, tmp_path):
    topics = AUDIT.taxonomy(content.CONTENT_DIR)
    source_path = tmp_path / "study/source-map.json"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(json.dumps({"schema_version": 1, "mappings": []}))
    originals = [{"id": "pre-a1-s-original"}, {"id": "pre-a1-s-adapted"},
                 {"id": "pre-a1-s-unmapped", "title": {"nl": "Een zus en familie"}}]
    monkeypatch.setattr(AUDIT, "banks", lambda root, stage: (originals, []) if stage == "pre-a1" else ([], []))
    monkeypatch.setattr(AUDIT, "validate_pack", lambda path, stage, known: [
        {"id": "pre-a1-family", "topic_id": "family", "source_id": "pre-a1-s-adapted"},
        {"id": "pre-a1-near-copy", "topic_id": "friends"},
    ] if stage == "pre-a1" else [])
    monkeypatch.setattr(AUDIT, "reading_lessons", lambda *args: {
        stage: [reading()] if stage == "pre-a1" else [] for stage in STAGE_IDS})
    monkeypatch.setattr(AUDIT, "reading_mappings", lambda *args: [
        {"stage_id": "pre-a1", "topic_id": "family", "story_id": "pre-a1-s-original"},
        {"stage_id": "pre-a1", "topic_id": "family", "story_id": "pre-a1-s-adapted"}])
    monkeypatch.setattr(story_inventory, "audit", lambda root: {"stages": [
        {"stage": stage, "legacy_library_eligible_story_ids": [item["id"] for item in originals]
         if stage == "pre-a1" else []} for stage in STAGE_IDS],
        "canonical_stories": [
            {"stage_id": "pre-a1", "source_kind": kind, "source_id": identifier, "eligible": valid}
            for kind, identifier, valid in (
                ("guided", "pre-a1-family", True),
                ("guided", "pre-a1-near-copy", False),
                ("reading", "pre-a1-read-sister-name", True),
                ("library", "pre-a1-s-original", True),
                ("library", "pre-a1-s-unmapped", True),
            )]})
    index = AUDIT.make_index(tmp_path, topics)
    assert index["stages"]["pre-a1"]["reading"]["family"] == [
        {"source": "pack", "id": "pre-a1-family"},
        {"source": "reading", "id": "pre-a1-read-sister-name"},
        {"source": "story", "id": "pre-a1-s-original"}]
    assert index["stages"]["pre-a1"]["speaking"]["family"] == [{"source": "pack", "id": "pre-a1-family"}]
    assert "pre-a1-s-unmapped" not in json.dumps(index)
    assert "friends" not in index["stages"]["pre-a1"]["reading"]
    assert index["stages"]["pre-a1"]["writing"]["friends"] == [
        {"source": "pack", "id": "pre-a1-near-copy"}]


@pytest.mark.parametrize("fault", [None, "missing", "duplicate", "excluded", "wrong_stage"])
def test_counted_story_must_be_reachable_once_in_its_actual_stage(fault):
    records = [
        {"stage_id": "a2", "source_kind": kind, "source_id": identity, "eligible": eligible}
        for kind, identity, eligible in (
            ("guided", "a2-guided", True),
            ("library", "a2-original", True),
            ("reading", "a2-read-new", True),
            ("guided", "a2-repeated", False),
        )
    ]
    references = [{"source": source, "id": identity} for source, identity in (
        ("pack", "a2-guided"), ("story", "a2-original"), ("reading", "a2-read-new"))]
    index = {"stages": {"a2": {"reading": {"family": references}}}}
    if fault == "missing":
        references.pop()
    elif fault == "duplicate":
        index["stages"]["a2"]["reading"]["friends"] = [references[-1]]
    elif fault == "excluded":
        references.append({"source": "pack", "id": "a2-repeated"})
    elif fault == "wrong_stage":
        index["stages"]["b1"] = {"reading": {"family": [references.pop()]}}
    if fault:
        with pytest.raises(ValueError, match="selectable catalogue exactly"):
            AUDIT.validate_reading_reachability(index, records)
    else:
        assert AUDIT.validate_reading_reachability(index, records) == {"a2": 3}
