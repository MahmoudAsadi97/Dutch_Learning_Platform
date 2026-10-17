"""Original source-linked lessons extend practice without rewriting banks or assessments."""
from __future__ import annotations

import hashlib
import json
import os
import re

import pytest
from pydantic import ValidationError

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import library, service, supplements, topics
from dlp.domains.curriculum.schemas import STAGE_IDS, Stage
from dlp.domains.exercises.schemas import CreateBody

STAGES = ("pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1")
UNITS = ("01", "02")


@pytest.mark.parametrize("topic_id", [*(f"{stage}-t001" for stage in STAGE_IDS),
                                      *(f"{stage}-t-source-{unit}" for stage in STAGES for unit in UNITS)])
def test_exercise_request_accepts_legacy_and_source_topic_syntax(topic_id):
    body = CreateBody(request_id="source-body-0001", source="topic", topic_id=topic_id, skill="reading")
    assert body.topic_id == topic_id


@pytest.mark.parametrize("topic_id", ("../a1-t-source-01", "a1-t-source-01/../../x", "a1-t-source-01?x=1",
                                     "a1-t-source-1", "a1-t-source-001", "a1-t-source-aa",
                                     "a1-t-source-01-r1", "a1-t-source-01.json", "a1-t1", "a1-t0001",
                                     "a1-t-source-01\n", "A1-t-source-01", "a1-t-story-01"))
def test_exercise_request_rejects_malformed_and_path_like_source_topic_ids(topic_id):
    with pytest.raises(ValidationError):
        CreateBody(request_id="source-body-0002", source="topic", topic_id=topic_id, skill="reading")


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("unit", UNITS)
@pytest.mark.parametrize("skill", ("reading", "listening"))
def test_source_topic_session_starts_completes_and_persists_progress(client, stage, unit, skill):
    from tests.conftest import auth_headers
    from tests.test_exercises_topic_completion import _create, _run

    topic_id = f"{stage}-t-source-{unit}"
    tag = f"source-session-{stage}-{unit}-{skill}"
    body = {"source": "topic", "stage_id": stage, "topic_id": topic_id, "skill": skill}
    assert client.post("/exercises/sessions", json={"request_id": tag, **body}).status_code == 401
    detail_url = f"/curriculum/{stage}/topics/{topic_id}"
    before = client.get(detail_url, params={"skill": skill}, headers=auth_headers())
    assert before.status_code == 200, before.text
    assert before.json()["progress"] == {"completed": False, "attempted": False}

    def checked_create(client, request_id, **requested):
        response = _create(client, request_id, source="topic", **requested)
        assert response.status_code == 201, response.text
        view = response.json()
        assert (view["stage_id"], view["topic_id"], view["skill"]) == (stage, topic_id, skill)
        passage, *questions = view["items"]
        assert passage["kind"] == ("read_passage" if skill == "reading" else "listen_passage")
        assert len(questions) == 2
        assert all(item["kind"] == "choice" and item["skill"] == skill for item in questions)
        def protected_fields(value):
            if isinstance(value, dict):
                return bool({"answer_index", "explanation", "positions"} & set(value)) or any(
                    protected_fields(child) for child in value.values())
            if isinstance(value, list):
                return any(protected_fields(child) for child in value)
            return False

        assert not protected_fields(view)
        # An explanation may quote the passage verbatim, especially at pre-A1. Those visible facts are
        # the task, not a leaked key; protect answer/explanation fields and unreleased feedback instead.
        assert all(item["feedback"] is None for item in questions)
        assert all(option.get("en") is None and option.get("fa") is None
                   for item in questions for option in item["prompt"]["options"])
        return response

    finished = _run(client, tag, [True, True], create=checked_create,
                    stage_id=stage, topic_id=topic_id, skill=skill)
    completion = finished["summary"]["completion"]
    assert completion["scope"] == "topic" and completion["topic_id"] == topic_id
    assert completion["skill"] == skill and completion["counted"] and completion["passed"]
    assert completion["correct"] == completion["required"] == completion["total"] == 2
    assert completion["completed"] and completion["to_retry"] == 0
    # These are fresh requests: completion must survive the POST transaction, not just appear in its response.
    after = client.get(detail_url, params={"skill": skill}, headers=auth_headers())
    assert after.status_code == 200, after.text
    assert after.json()["progress"] == {"completed": True, "attempted": True}
    assert all(set(question) == {"id", "prompt", "options"} for question in after.json()["activity"]["questions"])
    stored = client.get(f"/exercises/sessions/{finished['view']['id']}", headers=auth_headers())
    assert stored.status_code == 200, stored.text
    assert stored.json()["status"] == "finished"
    stage_progress = client.get(f"/curriculum/{stage}", headers=auth_headers())
    assert stage_progress.status_code == 200, stage_progress.text
    assert skill in stage_progress.json()["progress"]["practice_completed"]
    other_unit = next(other for other in UNITS if other != unit)
    separate = client.get(f"/curriculum/{stage}/topics/{stage}-t-source-{other_unit}",
                          params={"skill": skill}, headers=auth_headers())
    assert separate.status_code == 200, separate.text
    assert separate.json()["progress"] == {"completed": False, "attempted": False}


def test_source_topic_session_refuses_unknown_items_and_stage_mismatch(client):
    from tests.test_exercises_topic_completion import _create

    missing = _create(client, "source-missing-0001", source="topic", topic_id="a1-t-source-99", skill="reading")
    assert missing.status_code == 404, missing.text
    mismatch = _create(client, "source-mismatch-0001", source="topic", stage_id="pre-a1",
                       topic_id="a1-t-source-01", skill="reading")
    assert mismatch.status_code == 404, mismatch.text


@pytest.mark.parametrize("stage_id", STAGES)
def test_original_supplement_is_live_in_all_four_skills_and_story_time(stage_id):
    pack = json.loads((CONTENT_DIR / "source-lessons" / f"{stage_id}.json").read_text())
    merged = supplements.load(CONTENT_DIR, stage_id)
    bank = library.library_for(stage_id)
    topic_bank = topics.topics_for(stage_id)
    base_words = json.loads((CONTENT_DIR / "library" / f"{stage_id}.json").read_text())
    base_topics = json.loads((CONTENT_DIR / "practice" / f"{stage_id}.json").read_text())
    assert len(bank.vocabulary) == len(base_words["vocabulary"]) + len(merged["vocabulary"])
    assert len(pack["stories"]) == len(pack["topics"]) == len(UNITS)
    assert len(bank.stories) == len(base_words["stories"]) + len(merged["stories"])
    assert len(topic_bank.topics) == len(base_topics["topics"]) + len(merged["topics"])
    assert [word.id for word in bank.vocabulary[:len(base_words["vocabulary"])]] == [
        word["id"] for word in base_words["vocabulary"]]
    assert [story.id for story in bank.stories[:len(base_words["stories"])]] == [
        story["id"] for story in base_words["stories"]]
    assert [topic.id for topic in topic_bank.topics[:len(base_topics["topics"])]] == [
        topic["id"] for topic in base_topics["topics"]]
    assert {topic["id"] for topic in pack["topics"]} == {
        f"{stage_id}-t-source-{unit}" for unit in UNITS}
    assert {story["id"] for story in pack["stories"]} == {
        f"{stage_id}-s-source-{unit}" for unit in UNITS}
    assert len({topic["reading"]["text"]["nl"] for topic in pack["topics"]}) == len(UNITS)
    assert len({topic["listening"]["text"]["nl"] for topic in pack["topics"]}) == len(UNITS)
    assert library.story_page(bank, topic="Van woord naar gesprek")["total"] == len(UNITS)
    for unit in UNITS:
        topic = topics.topic_for(topic_bank, f"{stage_id}-t-source-{unit}")
        assert topics.review_of(topic_bank, "reading", topic) == {}
        assert topics.review_of(topic_bank, "listening", topic) == {}
        assert set(topic.vocabulary_ids).issubset({w.id for w in bank.vocabulary})
        assert topic.reading.text.nl != topic.listening.text.nl
        story = library.story_detail(bank, f"{stage_id}-s-source-{unit}")
        assert len(story["paragraphs"]) == 2
        assert set(story["vocabulary_ids"]) == set(topic.vocabulary_ids)
        for skill in ("speaking", "writing"):
            task = getattr(topic, skill)
            assert task.min_words <= len(task.sample.nl.split()) <= task.max_words
        for question in [*topic.reading.questions, *topic.listening.questions]:
            for language in ("nl", "en", "fa"):
                assert len({getattr(o, language) for o in question.options}) == len(question.options)


def test_grammar_examples_extend_existing_rules_without_touching_final_tests():
    original = json.loads((CONTENT_DIR / "curriculum/path.json").read_text())
    first = service.curriculum()
    second = service.curriculum()
    for before, after, again in zip(original["stages"], first.stages, second.stages, strict=True):
        assert after.test.model_dump() == Stage.model_validate(before).test.model_dump()
        assert after.model_dump() == again.model_dump()
        for rule in before["grammar"]:
            updated = next(g for g in after.grammar if g.id == rule["id"])
            assert [e.model_dump() for e in updated.examples[:len(rule["examples"])]] == rule["examples"]
            assert [q.model_dump() for q in updated.practice[:len(rule["practice"])]] == rule["practice"]
    assert len(supplements.curriculum_stamp(CONTENT_DIR)) == sum(
        len(list((CONTENT_DIR / directory).glob("*.json"))) for directory in supplements.DIRECTORIES)


def test_reference_pages_and_content_hashes_are_bound_to_supplied_sources():
    manifest = json.loads((CONTENT_DIR / "source-index/manifest.json").read_text())
    refs = {s["source_id"]: s for s in manifest["sources"]}
    stage_map = json.loads((CONTENT_DIR / "source-index/stage-map.json").read_text())
    concepts_by_stage = {s["id"]: set(s.get("source_concepts", [])) | set(s.get("source_concepts_recycled", []))
                         for s in stage_map["stages"]}
    links = json.loads((CONTENT_DIR / "source-index/lesson-links.json").read_text())["lessons"]
    concepts = json.loads((CONTENT_DIR / "source-index/concepts.json").read_text())
    concept_ids = {concept["id"] for concept in concepts["grammar"]}
    assert len(refs) == 9 and manifest["total_pages"] == 884
    assert {x["stage_id"] for x in links} == set(STAGES)
    assert len(links) == len(STAGES) * len(UNITS)
    assert {link["topic_id"] for link in links} == {
        f"{stage}-t-source-{unit}" for stage in STAGES for unit in UNITS}
    assert len({link["story_id"] for link in links}) == len(links)
    for link in links:
        assert link["concept"] in concepts_by_stage[link["stage_id"]]
        pack_path = CONTENT_DIR / "source-lessons" / f"{link['stage_id']}.json"
        assert hashlib.sha256(pack_path.read_bytes()).hexdigest() == link["pack_sha256"]
        assert link["language_review"] == "pending" and link["level_alignment"] == "provisional"
        pack = json.loads(pack_path.read_text())
        topic = next(item for item in pack["topics"] if item["id"] == link["topic_id"])
        story = next(item for item in pack["stories"] if item["id"] == link["story_id"])
        assert link["concept"] in concept_ids
        assert link["grammar_id"] in {rule["id"] for rule in pack["grammar_extensions"]}
        assert set(link["vocabulary_ids"]) == set(topic["vocabulary_ids"]) == set(story["vocabulary_ids"])
        assert link["sources"]
        for source in link["sources"]:
            assert source["source_sha256"] == refs[source["source_id"]]["sha256"]
            assert 1 <= source["pdf_page"] <= refs[source["source_id"]]["pdf_pages"]


def test_public_source_inventory_has_no_ocr_text_or_candidate_tokens():
    pages = json.loads((CONTENT_DIR / "source-index/pages.json").read_text())
    assert len(pages) == 884
    allowed = {"source_id", "pdf_page", "status", "word_count", "mean_word_confidence", "grammar_candidates"}
    assert all(set(page) == allowed for page in pages)


@pytest.mark.parametrize("stage_id", ("pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2"))
def test_beginner_scans_are_not_promoted_to_advanced_stage_content(stage_id):
    assert not (CONTENT_DIR / "source-lessons" / f"{stage_id}.json").exists()
    pack = supplements.load(CONTENT_DIR, stage_id)
    assert pack["grammar_extensions"] == []
    assert all("-t-source-" not in item["id"] for item in pack["topics"])


def test_mutating_a_returned_pack_does_not_modify_the_cached_source():
    pack = supplements.load(CONTENT_DIR, "a1")
    pack["topics"][0]["title"]["nl"] = "Changed"
    assert supplements.load(CONTENT_DIR, "a1")["topics"][0]["title"]["nl"] == "Woensdag om twee uur"


@pytest.mark.parametrize("field,value", [("stage_id", "c1"), ("review_status", "approved"), ("topics", "not a list")])
def test_invalid_or_falsely_approved_supplement_is_refused(tmp_path, field, value):
    folder = tmp_path / "source-lessons"
    folder.mkdir()
    data = supplements.load(CONTENT_DIR, "a1")
    data[field] = value
    (folder / "a1.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        supplements.load(tmp_path, "a1")


def test_library_and_topic_caches_notice_changed_supplements(tmp_path, monkeypatch):
    for directory in ("library", "practice", "source-lessons"):
        (tmp_path / directory).mkdir()
        source = CONTENT_DIR / directory / "a1.json"
        (tmp_path / directory / "a1.json").write_bytes(source.read_bytes())
    monkeypatch.setattr(library, "CONTENT_DIR", tmp_path)
    monkeypatch.setattr(topics, "CONTENT_DIR", tmp_path)
    first_story = library.story_detail(library.library_for("a1"), "a1-s-source-01")
    first_topic = topics.topic_for(topics.topics_for("a1"), "a1-t-source-01")
    assert first_story["title"]["nl"] == first_topic.title.nl == "Woensdag om twee uur"
    path = tmp_path / "source-lessons/a1.json"
    data = json.loads(path.read_text())
    for item in (data["topics"][-1], data["stories"][-1]):
        item["title"]["nl"] = "Een herziene afspraak"
    previous = path.stat().st_mtime_ns
    path.write_text(json.dumps(data), encoding="utf-8")
    os.utime(path, ns=(previous + 1_000_000_000, previous + 1_000_000_000))
    assert library.library_for("a1").stories[-1].title.nl == "Een herziene afspraak"
    assert topics.topics_for("a1").topics[-1].title.nl == "Een herziene afspraak"
    assert library.story_detail(library.library_for("a1"), "a1-s-source-01")["title"]["nl"] == "Woensdag om twee uur"
    assert topics.topic_for(topics.topics_for("a1"), "a1-t-source-01").title.nl == "Woensdag om twee uur"
    path.unlink()
    assert len(library.library_for("a1").stories) == 100
    assert len(topics.topics_for("a1").topics) == 100


@pytest.mark.parametrize("case", ("word-id", "story-id", "topic-id", "story-reference", "topic-reference",
                                  "grammar-question-id", "topic-question-id", "malformed-topic",
                                  "blank-grammar-translation", "duplicate-grammar", "unexpected-field", "not-object"))
def test_malformed_and_foreign_stage_items_are_refused_before_any_bank_is_cached(tmp_path, case):
    data = supplements.load(CONTENT_DIR, "a1")
    if case == "word-id":
        data["vocabulary"][0]["id"] = "c2-source-word"
    elif case == "story-id":
        data["stories"][0]["id"] = "c2-source-story"
    elif case == "topic-id":
        data["topics"][0]["id"] = "c2-t-source-01"
    elif case in ("story-reference", "topic-reference"):
        data["stories" if case == "story-reference" else "topics"][0]["vocabulary_ids"][0] = "c2-source-word"
    elif case == "grammar-question-id":
        data["grammar_extensions"][0]["practice"][0]["id"] = "c2-source-grammar-01"
    elif case == "topic-question-id":
        data["topics"][0]["reading"]["questions"][0]["id"] = "c2-t-source-01-r1"
    elif case == "malformed-topic":
        data["topics"][0].pop("listening")
    elif case == "blank-grammar-translation":
        data["grammar_extensions"][0]["examples"][0]["fa"] = " "
    elif case == "duplicate-grammar":
        data["grammar_extensions"].append(data["grammar_extensions"][0])
    elif case == "unexpected-field":
        data["test"] = {}
    else:
        data = []
    folder = tmp_path / "source-lessons"
    folder.mkdir()
    (folder / "a1.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        supplements.load(tmp_path, "a1")


def test_curriculum_cache_notices_grammar_changes_and_deletion(tmp_path, monkeypatch):
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "source-lessons").mkdir()
    original = CONTENT_DIR / "curriculum/path.json"
    (tmp_path / "curriculum/path.json").write_bytes(original.read_bytes())
    path = tmp_path / "source-lessons/a1.json"
    path.write_bytes((CONTENT_DIR / "source-lessons/a1.json").read_bytes())
    monkeypatch.setattr(service, "CONTENT_DIR", tmp_path)
    before = service.stage_for("a1")
    data = json.loads(path.read_text())
    rule_id = data["grammar_extensions"][0]["id"]
    old_example = data["grammar_extensions"][0]["examples"][0]["nl"]
    data["grammar_extensions"][0]["examples"][0]["nl"] = "De les begint om tien uur."
    previous = path.stat().st_mtime_ns
    path.write_text(json.dumps(data), encoding="utf-8")
    os.utime(path, ns=(previous + 1_000_000_000, previous + 1_000_000_000))
    after = service.stage_for("a1")
    updated = next(rule for rule in after.grammar if rule.id == rule_id)
    assert old_example not in [example.nl for example in updated.examples]
    assert "De les begint om tien uur." in [example.nl for example in updated.examples]
    assert before.test == after.test
    path.unlink()
    base = next(stage for stage in json.loads(original.read_text())["stages"] if stage["id"] == "a1")
    assert service.stage_for("a1").model_dump() == Stage.model_validate(base).model_dump()


def test_review_detection_includes_prior_stage_supplements_and_cache_changes(tmp_path, monkeypatch):
    for directory in ("library", "practice", "source-lessons"):
        (tmp_path / directory).mkdir()
        for stage in ("pre-a1", "a1"):
            (tmp_path / directory / f"{stage}.json").write_bytes((CONTENT_DIR / directory / f"{stage}.json").read_bytes())
    monkeypatch.setattr(library, "CONTENT_DIR", tmp_path)
    monkeypatch.setattr(topics, "CONTENT_DIR", tmp_path)
    bank = topics.topics_for("a1")
    topic = topics.topic_for(bank, "a1-t-source-01")
    assert topics.review_of(bank, "reading", topic) == {}
    path = tmp_path / "source-lessons/pre-a1.json"
    data = json.loads(path.read_text())
    data["topics"][0]["reading"]["text"] = topic.reading.text.model_dump()
    previous = path.stat().st_mtime_ns
    path.write_text(json.dumps(data), encoding="utf-8")
    os.utime(path, ns=(previous + 1_000_000_000, previous + 1_000_000_000))
    assert topics.review_of(bank, "reading", topic) == {
        topic.id: {"stage_id": "pre-a1", "topic_id": "pre-a1-t-source-01"},
    }
    path.unlink()
    assert topics.review_of(bank, "reading", topic) == {}


def test_prior_stage_review_lookup_refuses_an_invalid_topic_bank(tmp_path):
    (tmp_path / "practice").mkdir()
    path = tmp_path / "practice/a1.json"
    data = json.loads((CONTENT_DIR / "practice/a1.json").read_text())
    data["topics"][0]["id"] = "c2-t-foreign"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        topics._texts(str(path), path.stat().st_mtime_ns, "reading")


def test_new_target_words_really_occur_in_their_story():
    variants = {"spellen": ("spel", "spellen"), "kopen": ("gekocht", "koop", "kopen")}
    for stage in STAGES:
        pack = json.loads((CONTENT_DIR / "source-lessons" / f"{stage}.json").read_text())
        for word in pack["vocabulary"]:
            lemma = re.sub(r"^(de|het|een) ", "", word["term"].casefold())
            linked_stories = [story for story in pack["stories"] if word["id"] in story["vocabulary_ids"]]
            assert linked_stories, word["id"]
            for linked in linked_stories:
                story = " ".join(p["nl"] for p in linked["paragraphs"]).casefold()
                assert any(re.search(r"\b" + re.escape(form) + r"\b", story)
                           for form in variants.get(lemma, (lemma,))), (lemma, linked["id"])


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("unit", UNITS)
def test_supplement_routes_use_existing_auth_and_hide_receptive_keys(client, headers, stage, unit):
    base = f"/curriculum/{stage}/topics/{stage}-t-source-{unit}"
    assert client.get(base, params={"skill": "reading"}).status_code == 401
    for skill in ("reading", "listening", "speaking", "writing"):
        response = client.get(base, params={"skill": skill}, headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["review_status"] == "unreviewed"
        assert data["review_of"] is None
        if skill in ("reading", "listening"):
            assert all(set(q) == {"id", "prompt", "options"} for q in data["activity"]["questions"])
        else:
            assert data["context"]["reading"]["nl"] and data["context"]["listening"]["nl"]


def test_connected_tasks_keep_known_facts_and_requested_actions_consistent():
    a2 = supplements.load(CONTENT_DIR, 'a2')
    topic = a2['topics'][0]
    assert 'thuiskwam' in topic['reading']['text']['nl']
    assert 'thuis kwam' not in topic['reading']['text']['nl']
    for language, ownership in (('nl', 'wat je moet meenemen'), ('en', 'ask what to bring'),
                                ('fa', 'چه چیزی باید همراه بیاورید')):
        assert ownership in topic['writing']['prompt'][language]
    b1 = supplements.load(CONTENT_DIR, 'b1')['topics'][0]
    for language, bus, time in (('nl', 'bus acht', '15.10'), ('en', 'bus eight', '15:10'),
                                ('fa', 'اتوبوس شماره هشت', '۱۵:۱۰')):
        for text in (b1['reading']['text'][language], b1['speaking']['sample'][language],
                     b1['writing']['sample'][language]):
            assert bus in text and time in text


def test_content_audit_counts_the_same_effective_banks_as_the_application():
    import importlib.util

    spec = importlib.util.spec_from_file_location("content_audit", CONTENT_DIR.parent / "scripts/audit_learning_content.py")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    result = audit.audit(CONTENT_DIR)
    assert result["schema_version"] == 2
    for row in result["stages"]:
        stage = row["stage"]
        bank = library.library_for(stage)
        assert row["vocabulary"] == len(bank.vocabulary)
        assert row["stories"] == len(bank.stories)
        assert row["topics_per_skill"] == len(topics.topics_for(stage).topics)
        assert bool(row["content_sha256"]["supplement"]) == (stage in STAGES)
