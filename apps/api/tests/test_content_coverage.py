"""Learner-visible availability must agree with validated banks and the editorial audit."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import coverage, library, service, story_inventory, topics
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS

ROOT = Path(__file__).resolve().parents[3]


def test_published_coverage_matches_effective_banks_and_shared_story_audit():
    rows = coverage.all_coverage()
    audit_rows = {row["stage"]: row for row in story_inventory.audit(CONTENT_DIR)["stages"]}
    assert tuple(rows) == STAGE_IDS
    for stage in service.curriculum().stages:
        row = rows[stage.id]
        bank = library.library_for(stage.id)
        practice = topics.topics_for(stage.id)
        audit = audit_rows[stage.id]
        assert row["words"] == len(bank.vocabulary)
        assert row["productive_core"] == sum(word.productive_core for word in bank.vocabulary)
        assert row["productive_contexts"] == sum(len(word.contexts) for word in bank.vocabulary if word.productive_core)
        assert row["total_stories"] == len(bank.stories)
        assert row["authored_stories"] == audit["authored_stories"]
        assert row["eligible_authored_stories"] == audit["eligible_authored_stories"]
        assert row["legacy_stories"] == audit["legacy_stories"]
        assert row["grammar_questions"] == sum(len(rule.practice) for rule in stage.grammar)
        assert row["skill_topics"] == {skill: len(practice.topics) for skill in SKILLS}
        assert row["shortfalls"]["authored_stories"] == audit["authored_story_shortfall"]
        assert row["targets"] == coverage.TARGETS
        assert row["review_status"] == "unreviewed"
    # These checks deliberately expose the authored-story shortfall instead of padding it with old templates.
    assert all(row["grammar_questions"] >= 100 for row in rows.values())
    assert all(row["productive_core"] >= 150 for row in rows.values())


def test_ineligible_and_legacy_stories_never_satisfy_the_authored_target():
    stage = SimpleNamespace(grammar=[SimpleNamespace(practice=[None] * 5)])
    bank = SimpleNamespace(vocabulary=[SimpleNamespace(productive_core=True, contexts=[None] * 3),
                                      SimpleNamespace(productive_core=False, contexts=[])],
                           stories=[None] * 250, review_status="unreviewed")
    practice = SimpleNamespace(topics=[None] * 12)
    row = coverage.stage_coverage(stage, bank, practice,
                                  {"authored_stories": 201, "eligible_authored_stories": 199, "legacy_stories": 49})
    assert row["total_stories"] == 250 and row["authored_stories"] == 201
    assert row["eligible_authored_stories"] == 199
    assert row["shortfalls"] == {"words": 498, "productive_core": 149, "grammar_questions": 95,
                                "authored_stories": 1, "skill_topics": dict.fromkeys(SKILLS, 88)}
    assert row["productive_contexts"] == 3
    assert row["targets"]["authored_stories"] == 200


def test_coverage_report_contains_counts_not_assessment_answers_or_mastery_claims():
    report = coverage.report()
    assert [row["stage_id"] for row in report["stages"]] == list(STAGE_IDS)
    assert "CEFR" in report["claim"] and "do not" in report["claim"]
    serialized = json.dumps(report)
    for forbidden in ("answer_index", "sample", "passed", "learner_key", "certificate"):
        assert forbidden not in serialized


@pytest.mark.parametrize("path", ["curriculum/path.json", "alignment/story-provenance.json",
                                  *[f"{directory}/a2.json" for directory in coverage.DIRECTORIES]])
def test_every_relevant_source_invalidates_coverage_cache_key(tmp_path, path):
    file = tmp_path / path
    file.parent.mkdir(parents=True)
    before = coverage.content_stamp(tmp_path)
    file.write_text("{}")
    created = coverage.content_stamp(tmp_path)
    assert created != before
    assert any(key == path for key, _, _ in created)
    file.write_text('{"changed": true}')
    assert coverage.content_stamp(tmp_path) != created
    file.unlink()
    assert coverage.content_stamp(tmp_path) == before


def test_hot_inventory_is_cached_without_repeating_story_similarity_audit(monkeypatch):
    coverage._read.cache_clear()
    coverage._story_audit.cache_clear()
    calls = []
    original = story_inventory.audit

    def audit(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(story_inventory, "audit", audit)
    assert coverage.all_coverage() == coverage.all_coverage()
    assert len(calls) == 1


def test_cli_import_and_runtime_use_identical_story_eligibility_rules():
    spec = importlib.util.spec_from_file_location("coverage_story_cli", ROOT / "scripts/validate_story_quality.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.audit is story_inventory.audit
    assert module.normal is story_inventory.normal
    assert module.shingles is story_inventory.shingles


def test_inventory_reference_requires_identity_and_has_no_learner_rows(client, headers):
    assert client.get("/curriculum/reference/coverage").status_code == 401
    response = client.get("/curriculum/reference/coverage", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) == 12
    assert "learner_key" not in data and "answer_index" not in response.text


def test_catalogue_stage_and_reference_expose_same_current_counts(client, headers):
    catalog = client.get("/curriculum", headers=headers)
    assert catalog.status_code == 200
    expected = coverage.all_coverage()
    for stage in catalog.json()["stages"]:
        assert stage["coverage"] == expected[stage["id"]]
        assert stage["unlocked"] is True
    selected = client.get("/curriculum/pre-a2", headers=headers)
    assert selected.status_code == 200
    assert selected.json()["coverage"] == expected["pre-a2"]
    assert "test" not in selected.json()


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_authored_story_collection_is_reachable_and_matches_qualified_inventory(stage_id):
    bank = library.library_for(stage_id)
    eligible = coverage.eligible_story_ids(stage_id)
    page = library.story_page(bank, authored_only=True, limit=30)
    assert page["authored_only"] is True
    assert page["total"] == coverage.all_coverage()[stage_id]["eligible_authored_stories"]
    assert {item["id"] for item in page["items"]}.issubset(eligible)
    assert all(8 <= item["line_count"] <= 12 for item in page["items"])
    overview = library.summary(bank)
    assert overview["eligible_authored_story_count"] == page["total"]
    assert sum(topic["eligible_authored_story_count"] for topic in overview["topics"]) == page["total"]
    assert overview["story_count"] == overview["authored_story_count"] + overview["legacy_story_count"]
    assert library.story_page(bank)["total"] == len(bank.stories)


def test_audit_exclusions_are_applied_before_story_pagination(monkeypatch):
    bank = library.library_for("pre-a1")
    authored = [item for item in bank.stories if item.lines is not None]
    # Model an audit finding: a story with valid line counts may still be an excluded near-copy.
    permitted = frozenset(item.id for item in authored[1:4])
    monkeypatch.setattr(coverage, "eligible_story_ids", lambda stage_id: permitted)
    page = library.story_page(bank, authored_only=True, offset=1, limit=1)
    assert page["total"] == 3
    assert [item["id"] for item in page["items"]] == [authored[2].id]
    assert library.story_page(bank, authored_only=True, query=authored[0].title.nl)["total"] == 0
    assert library.story_page(bank, authored_only=False)["total"] == len(bank.stories)


def test_authored_story_api_keeps_full_bank_as_explicit_compatible_option(client, headers):
    filtered = client.get("/library/pre-a2/stories?authored_only=true", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["authored_only"] is True
    assert filtered.json()["total"] == coverage.all_coverage()["pre-a2"]["eligible_authored_stories"]
    all_stories = client.get("/library/pre-a2/stories", headers=headers)
    assert all_stories.status_code == 200
    assert all_stories.json()["authored_only"] is False
    assert all_stories.json()["total"] == coverage.all_coverage()["pre-a2"]["total_stories"]
    assert client.get("/library/pre-a2/stories?authored_only=invalid", headers=headers).status_code == 422
