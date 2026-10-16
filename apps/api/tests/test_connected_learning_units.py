"""Exercise real authored stories and their four-skill links without granting reading credit."""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import library, supplements, topics
from dlp.domains.curriculum.library import LibraryStory
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.schemas import CreateBody


def pack(stage):
    return json.loads((CONTENT_DIR / "learning-units" / f"{stage}.json").read_text(encoding="utf-8"))


def authoring_module(name):
    source = CONTENT_DIR.parent / "scripts" / "content_build" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("stage", STAGE_IDS)
def test_connected_units_are_stage_bound_parallel_and_not_a_claim_of_200_complete_stories(stage):
    data = pack(stage)
    bank = library.library_for(stage)
    topic_bank = topics.topics_for(stage)
    assert data["review_status"] == "unreviewed"
    assert len(data["stories"]) == len(data["topics"]) >= 2
    assert library.summary(bank)["authored_story_count"] == len(data["stories"])
    assert library.summary(bank)["target_story_count"] == 200
    assert len(bank.vocabulary) >= 500
    for story in data["stories"]:
        view = library.story_detail(bank, story["id"])
        assert len(view["lines"]) == 10
        assert len(view["paragraphs"]) == 2
        linked = topics.topic_for(topic_bank, view["topic_id"])
        assert set(linked.vocabulary_ids) == set(view["vocabulary_ids"])
        assert linked.reading.text.nl == "\n\n".join(p["nl"] for p in view["paragraphs"])
        assert linked.reading.text.nl != linked.listening.text.nl
        for skill in ("reading", "listening", "speaking", "writing"):
            CreateBody(request_id="connected-unit-test-01", source="topic", stage_id=stage,
                       topic_id=linked.id, skill=skill)
        for language in ("nl", "en", "fa"):
            assert all(line[language].strip() for line in view["lines"])
            assert " ".join(line[language] for line in view["lines"]) == " ".join(
                paragraph[language] for paragraph in view["paragraphs"])
        # No recognition, mastery or skill result is fabricated by library browsing.
        assert not {"completed", "passed", "mastered", "score"} & view.keys()


def test_authored_units_have_distinct_titles_and_text_across_all_stages():
    all_stories = [story for stage in STAGE_IDS for story in pack(stage)["stories"]]
    assert len(all_stories) >= 24
    for getter in (lambda s: s["title"]["nl"], lambda s: " ".join(line["nl"] for line in s["lines"])):
        values = [library.normalise(getter(story)) for story in all_stories]
        assert len(set(values)) == len(values)


def test_known_translation_and_word_sense_regressions_stay_fixed():
    def topic(stage, slug):
        return next(value for value in pack(stage)["topics"] if value["id"].endswith(slug))

    def narrative(stage, slug):
        return next(value for value in pack(stage)["stories"] if value["id"].endswith(slug))

    assert "in de avond" in topic("pre-b2", "empty-chair")["listening"]["text"]["nl"]
    assert "in de vooravond" in topic("b2", "balcony-rehearsal")["listening"]["text"]["nl"]
    assert "پیشنهاد شده" in topic("c1", "borrowed-view")["listening"]["text"]["fa"]
    assert "شیشه" in narrative("b2", "unnamed-photograph")["lines"][4]["fa"]
    assert "آینه" not in narrative("b2", "unnamed-photograph")["lines"][4]["fa"]
    assert "انحراف" in narrative("pre-c2", "map-for-two")["lines"][4]["fa"]
    assert "نمی‌خواهد" in narrative("pre-c1", "second-voice")["lines"][7]["fa"]
    story = narrative("a1", "window-plant")
    words = library.story_detail(library.library_for("a1"), story["id"])["vocabulary"]
    assert not any(word["term"] == "licht" for word in words)
    small = next(word for word in words if word["term"] == "klein")
    assert small["meaning"]["en"] == "small"


def test_builder_checks_runtime_contracts_before_writing_any_stage(tmp_path):
    for directory in ("alignment", "library", "source-lessons"):
        folder = tmp_path / "content" / directory
        folder.mkdir(parents=True)
        for name in ("learning-design.json",) if directory == "alignment" else ("pre-a1.json", "a1.json"):
            (folder / name).write_bytes((CONTENT_DIR / directory / name).read_bytes())
    valid, invalid = deepcopy(authoring_module("learning_units_lower").UNITS[:2])
    invalid["speaking_bounds"] = (1, 101)
    with pytest.raises(ValidationError, match="bounded recording"):
        authoring_module("learning_units").build(tmp_path, [valid, invalid])
    assert not (tmp_path / "content/learning-units").exists()


@pytest.mark.parametrize("case", ("short", "long", "translation", "paragraph", "audio"))
def test_line_contract_refuses_padding_and_divergent_translations(case):
    story = deepcopy(pack("pre-a1")["stories"][0])
    if case == "short":
        story["lines"] = story["lines"][:7]
    elif case == "long":
        story["lines"] *= 2
    elif case == "translation":
        story["lines"][0]["fa"] = ""
    elif case == "paragraph":
        story["paragraphs"][0]["en"] = "A different event."
    else:
        story["lines"][0]["nl"] = "woord " * 150
        story["paragraphs"][0]["nl"] = " ".join(line["nl"] for line in story["lines"][:5])
    with pytest.raises(ValidationError):
        LibraryStory.model_validate(story)


def test_new_unit_cache_tracks_change_and_deletion(tmp_path, monkeypatch):
    for directory in ("library", "practice", "source-lessons", "learning-units"):
        (tmp_path / directory).mkdir()
        source = CONTENT_DIR / directory / "a1.json"
        (tmp_path / directory / "a1.json").write_bytes(source.read_bytes())
    monkeypatch.setattr(library, "CONTENT_DIR", tmp_path)
    monkeypatch.setattr(topics, "CONTENT_DIR", tmp_path)
    data = pack("a1")
    story_id = data["stories"][0]["id"]
    assert library.story_detail(library.library_for("a1"), story_id)["lines"] == data["stories"][0]["lines"]
    path = tmp_path / "learning-units/a1.json"
    data["stories"][0]["title"]["nl"] = "Een gewijzigde titel"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert library.story_detail(library.library_for("a1"), story_id)["title"]["nl"] == "Een gewijzigde titel"
    path.unlink()
    assert library.summary(library.library_for("a1"))["authored_story_count"] == 0
    assert all("-t-unit-" not in topic.id for topic in topics.topics_for("a1").topics)
    assert not supplements.load(tmp_path, "a1")["stories"][-1].get("lines")


@pytest.mark.parametrize("case", ("missing-link", "foreign-stage", "different-text", "different-targets", "no-lines"))
def test_connected_pack_cannot_link_an_unrelated_or_foreign_practice(tmp_path, case):
    data = pack("a1")
    story = data["stories"][0]
    if case == "missing-link":
        story["topic_id"] = "a1-t-unit-does-not-exist"
    elif case == "foreign-stage":
        story["topic_id"] = "c2-t-unit-other-story"
    elif case == "different-text":
        data["topics"][0]["reading"]["text"]["en"] = "An unrelated story."
    elif case == "different-targets":
        data["topics"][0]["vocabulary_ids"] = data["topics"][0]["vocabulary_ids"][:1]
    else:
        story.pop("lines")
    directory = tmp_path / "learning-units"
    directory.mkdir()
    (directory / "a1.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        supplements.load(tmp_path, "a1")


@pytest.mark.parametrize("stage", STAGE_IDS)
@pytest.mark.parametrize("skill", ("reading", "listening"))
def test_connected_story_skill_can_complete_a_real_session(client, stage, skill):
    from tests.conftest import auth_headers
    from tests.test_exercises_topic_completion import _create, _run

    topic_id = pack(stage)["topics"][0]["id"]
    tag = f"connected-{stage}-{skill}"

    def create(client, request_id, **requested):
        response = _create(client, request_id, source="topic", **requested)
        assert response.status_code == 201, response.text
        assert len(response.json()["items"]) == 3
        return response

    finished = _run(client, tag, [True, True], create=create, stage_id=stage, topic_id=topic_id, skill=skill)
    completion = finished["summary"]["completion"]
    assert completion["counted"] and completion["passed"] and completion["skill"] == skill
    saved = client.get(f"/curriculum/{stage}/topics/{topic_id}", params={"skill": skill}, headers=auth_headers())
    assert saved.status_code == 200 and saved.json()["progress"]["completed"]
