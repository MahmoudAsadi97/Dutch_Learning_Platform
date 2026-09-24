"""Original four-skill packs and authoritative non-booking conversations."""
import pytest
from pydantic import ValidationError

from dlp.domains.content.schemas import MissionDocument
from dlp.domains.content.service import MISSIONS_DIR, read_mission_file
from dlp.domains.practice.actions import AppointmentState, ProposedAction, apply_action, required_actions_completed
from dlp.domains.practice.prompts import PROPOSE_ACTION_VERSION
from dlp.domains.practice.workflow import run_turn
from dlp.providers.fixtures import FixtureChatModel
from tests.conftest import auth_headers

PACKS = ["lunch-order", "shop-return", "course-message"]


@pytest.fixture(params=PACKS)
def pack(request):
    return read_mission_file(MISSIONS_DIR / request.param / "mission.json")


def test_pack_has_four_skills_answerable_questions_and_review_labels(pack):
    assert {s.skill for s in pack.steps} == {"reading", "listening", "speaking", "writing"}
    assert pack.fixed_dutch_word_count() <= 300
    assert all(t.review_status == "unreviewed" for _, t in pack.iter_localized())
    for step in pack.steps:
        assert step.instructions.fa
        if step.payload.type in {"reading", "listening"}:
            assert len(step.payload.questions) >= 2
            assert all(0 <= q.answer_index < len(q.options) for q in step.payload.questions)
    assert pack.scenario("base").setting.nl != pack.scenario("transfer").setting.nl
    assert not pack.steps[-1].payload.restrictions.help_ladder
    assert not pack.steps[-1].payload.restrictions.typed_fallback


def test_unavailable_choices_and_early_confirmation_cannot_complete(pack):
    scenario = pack.scenario("base")
    state = AppointmentState()
    assert not apply_action(scenario, state, ProposedAction(action="confirm")).accepted
    assert not apply_action(scenario, state, ProposedAction(action="choose_option", choice_id=scenario.choices[0].id)).accepted
    assert apply_action(scenario, state, ProposedAction(action="state_need", reason_text="Ik heb een vraag.")).accepted
    assert not apply_action(scenario, state, ProposedAction(action="choose_option", choice_id="invented")).accepted
    assert not required_actions_completed(state, ["state_need", "choose_option", "confirm"])


def test_service_selection_confirmation_change_and_cancel(pack):
    scenario = pack.scenario("base")
    state = AppointmentState()
    apply_action(scenario, state, ProposedAction(action="state_need", reason_text="Ik heb een vraag."))
    apply_action(scenario, state, ProposedAction(action="choose_option", choice_id=scenario.choices[0].id))
    assert not state.confirmed
    assert apply_action(scenario, state, ProposedAction(action="confirm")).accepted
    assert required_actions_completed(state, ["state_need", "choose_option", "confirm"])
    assert AppointmentState.from_dict(state.as_dict()).selected_choice_id == scenario.choices[0].id
    apply_action(scenario, state, ProposedAction(action="choose_option", choice_id=scenario.choices[1].id))
    assert not state.confirmed
    apply_action(scenario, state, ProposedAction(action="cancel"))
    assert not required_actions_completed(state, ["state_need", "choose_option", "confirm"])
    assert not apply_action(scenario, state, ProposedAction(action="confirm")).accepted


def test_service_workflow_uses_validated_choices_and_only_one_model_call(pack):
    scenario = pack.scenario("base")
    choice = scenario.choices[0]
    chat = FixtureChatModel(replies={PROPOSE_ACTION_VERSION: {"action": "choose_option", "choice_id": choice.id}})
    outcome = run_turn(chat, scenario=scenario, appointment={"reason_stated": True, "actions": ["state_need"]},
                       history=[], learner_text=choice.label.nl, request_id="choice-test")
    assert outcome["action_result"]["accepted"]
    assert choice.label.nl in outcome["reply_nl"]
    assert "Klopt dat?" in outcome["reply_nl"]
    assert len(chat.calls) == 1
    assert not outcome["appointment"]["confirmed"]


def test_schema_rejects_duplicate_choices_and_missing_phase(pack):
    raw = pack.model_dump(mode="json")
    raw["scenarios"][0]["choices"][1]["id"] = raw["scenarios"][0]["choices"][0]["id"]
    with pytest.raises(ValidationError, match="unique"):
        MissionDocument.model_validate(raw)
    raw = pack.model_dump(mode="json")
    raw["scenarios"][0]["fixed_lines"] = raw["scenarios"][0]["fixed_lines"][:3]
    with pytest.raises(ValidationError, match="every conversation phase"):
        MissionDocument.model_validate(raw)


@pytest.mark.parametrize("mission_id", PACKS)
def test_catalog_and_reading_progress_are_scoped_to_mission(client, mission_id):
    catalog = client.get("/missions", headers=auth_headers()).json()
    assert set(PACKS) <= {m["id"] for m in catalog["missions"]}
    response = client.post("/practice/sessions", headers=auth_headers(f"start-{mission_id}"),
                           json={"mission_id": mission_id, "variant": "base"})
    assert response.status_code == 201, response.text
    detail = response.json()
    assert detail["session"]["mission_id"] == mission_id
    assert detail["conversation"][0]["scenario_kind"] == "service"
    assert len(detail["conversation"][0]["choices"]) == 2
    assert detail["conversation"][0]["slots"] == []
    session_id = detail["session"]["id"]
    document = read_mission_file(MISSIONS_DIR / mission_id / "mission.json")
    for question in document.steps[0].payload.questions:
        answered = client.post(f"/practice/sessions/{session_id}/answers",
                               headers=auth_headers(f"answer-{mission_id}-{question.id}"),
                               json={"step_key": "read", "question_id": question.id,
                                     "chosen_index": question.answer_index})
        assert answered.status_code == 200, answered.text
    client.get("/missions/appointment-change", headers=auth_headers())
    records = client.get("/progress", headers=auth_headers()).json()["skill_records"]
    assert next(r for r in records if r["mission_id"] == mission_id and r["skill"] == "reading")["status"] == "practised"
    assert all(r["status"] == "not_started" for r in records if r["mission_id"] == "appointment-change")
