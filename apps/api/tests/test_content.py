import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dlp.domains.content.acceptance import check_a01
from dlp.domains.content.schemas import SKILLS, MissionDocument, review_summary
from dlp.domains.content.service import MISSIONS_DIR, ContentError, content_hash, read_mission_file

MISSION_PATH = MISSIONS_DIR / "appointment-change" / "mission.json"


@pytest.fixture(scope="module")
def raw() -> dict:
    return json.loads(Path(MISSION_PATH).read_text(encoding="utf-8"))


def test_fixture_validates_and_is_within_word_limit(raw):
    document = read_mission_file(MISSION_PATH)
    assert document.id == "appointment-change"
    assert document.fixed_dutch_word_count() < 300
    assert document.fixed_dutch_word_count() <= document.content_pack.word_limit
    assert {step.skill for step in document.steps} == set(SKILLS)


def test_every_fixed_text_is_labelled_unreviewed(raw):
    document = MissionDocument.model_validate(raw)
    summary = review_summary(document)
    assert summary.total_texts > 40
    assert summary.unreviewed == summary.total_texts
    assert all(text.label == "Niet-nagekeken inhoud" for _, text in document.iter_localized())


def test_help_ladder_is_persian_and_rtl_and_absent_in_checkpoint(raw):
    document = MissionDocument.model_validate(raw)
    for step in document.steps:
        rungs = getattr(step.payload, "help", None)
        if step.payload.type == "checkpoint":
            assert rungs is None
            assert step.payload.restrictions.help_ladder is False
            assert step.payload.restrictions.retry is False
            continue
        assert rungs is not None
        assert [r.level for r in rungs] == [1, 2, 3]
        assert all(r.direction == "rtl" for r in rungs if r.kind != "hint_nl")


def test_content_hash_is_stable_across_key_order(raw):
    document = MissionDocument.model_validate(raw)
    reordered = MissionDocument.model_validate(json.loads(json.dumps(raw, sort_keys=True)))
    assert content_hash(document) == content_hash(reordered)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d["steps"].pop(0), "completion references unknown step"),
        (lambda d: d["steps"].__setitem__(0, {**d["steps"][0], "skill": "listening", "payload": {**d["steps"][0]["payload"]}}), "does not match payload"),
        (lambda d: d["scenarios"].pop(1), "at least 2 items"),
        (lambda d: d["scenarios"][1].__setitem__("variant", "base"), "exactly one base and one transfer"),
        (lambda d: d["completion"].__setitem__("checkpoint_step_key", "read-reminder"), "must point at a checkpoint"),
        (lambda d: d["steps"][2]["payload"].__setitem__("required_actions", ["fly"]), "not allowed by"),
        (lambda d: d["scenarios"][0]["available_slots"][0].__setitem__("day", "2020-01-01"), "before the scenario reference date"),
        (lambda d: d["steps"][0]["payload"]["help"][1].__setitem__("direction", "ltr"), "must be rtl"),
        (lambda d: d["steps"][0]["payload"]["questions"][0].__setitem__("answer_index", 9), "out of range"),
        (lambda d: d["steps"][0].__setitem__("unknown_field", 1), "Extra inputs are not permitted"),
    ],
)
def test_schema_rejects_broken_documents(raw, mutate, message):
    broken = copy.deepcopy(raw)
    mutate(broken)
    with pytest.raises(ValidationError) as excinfo:
        MissionDocument.model_validate(broken)
    assert message in str(excinfo.value)


def test_word_limit_is_enforced_on_load(raw, tmp_path):
    bloated = copy.deepcopy(raw)
    bloated["steps"][0]["payload"]["text"]["nl"] = "woord " * 400
    path = tmp_path / "mission.json"
    path.write_text(json.dumps(bloated), encoding="utf-8")
    with pytest.raises(ContentError, match="limit is 300"):
        read_mission_file(path)


def test_acceptance_a01_passes_against_loaded_database(database):
    from dlp.db.session import session_scope

    with session_scope() as session:
        report = check_a01(session, "appointment-change")
    failed = [item for item in report.items if not item.passed]
    assert report.passed, failed
    assert {item.name for item in report.items} >= {
        "file_validates", "stored_in_database", "content_hash_matches", "normalised_steps_match",
        "pack_within_word_limit", "four_skills_covered", "base_and_transfer_variants",
    }
