from datetime import date, datetime, time

import pytest

from dlp.domains.content.service import MISSIONS_DIR, read_mission_file
from dlp.domains.practice.actions import AppointmentState, ProposedAction, apply_action, required_actions_completed


@pytest.fixture(scope="module")
def scenario():
    return read_mission_file(MISSIONS_DIR / "appointment-change" / "mission.json").scenario("dentist-base")


def test_happy_path_reason_offer_accept_confirm(scenario):
    state = AppointmentState()
    assert apply_action(scenario, state, ProposedAction(action="state_reason", reason_text="Ik moet werken.")).accepted
    assert apply_action(scenario, state, ProposedAction(action="propose_slot", slot_id="thu-1000")).accepted
    accepted = apply_action(scenario, state, ProposedAction(action="accept_slot", slot_id="thu-1000"))
    assert accepted.accepted and accepted.slot_id == "thu-1000" and not state.confirmed
    confirmed = apply_action(scenario, state, ProposedAction(action="confirm"))
    assert confirmed.accepted and state.confirmed
    assert required_actions_completed(state, ["state_reason", "accept_slot", "confirm"])


def test_model_cannot_invent_slots(scenario):
    state = AppointmentState()
    result = apply_action(scenario, state, ProposedAction(action="accept_slot", slot_id="sun-0300"))
    assert not result.accepted and "not an available slot" in result.reason
    result = apply_action(scenario, state, ProposedAction(action="accept_slot", proposed_day=date(2026, 9, 24),
                                                          proposed_time=time(11, 0)))
    assert not result.accepted
    ok = apply_action(scenario, state, ProposedAction(action="accept_slot", proposed_day=date(2026, 9, 24),
                                                      proposed_time=time(10, 0)))
    assert ok.accepted and ok.slot_id == "thu-1000"


def test_confirm_requires_an_accepted_slot(scenario):
    state = AppointmentState()
    result = apply_action(scenario, state, ProposedAction(action="confirm"))
    assert not result.accepted and "nothing to confirm" in result.reason
    assert not required_actions_completed(state, ["confirm"])


def test_only_offered_slots_can_be_accepted_once_offers_were_made(scenario):
    state = AppointmentState()
    apply_action(scenario, state, ProposedAction(action="propose_slot", slot_id="fri-1630"))
    result = apply_action(scenario, state, ProposedAction(action="accept_slot", slot_id="tue-0900"))
    assert not result.accepted and "never offered" in result.reason


def test_disallowed_and_empty_actions(scenario):
    state = AppointmentState()
    assert not apply_action(scenario, state, ProposedAction(action="none")).accepted
    assert not apply_action(scenario, state, ProposedAction(action="state_reason", reason_text="  ")).accepted
    cancelled = apply_action(scenario, state, ProposedAction(action="cancel"))
    assert cancelled.accepted and state.cancelled
    assert not apply_action(scenario, state, ProposedAction(action="confirm")).accepted


def test_state_round_trips_through_json(scenario):
    state = AppointmentState()
    apply_action(scenario, state, ProposedAction(action="state_reason", reason_text="ziek"))
    restored = AppointmentState.from_dict(state.as_dict())
    assert restored == state


def test_slot_from_another_scenario_is_refused(scenario):
    """`mon-1700` exists only in the hairdresser scenario; the dentist scenario must not accept it."""
    state = AppointmentState()
    result = apply_action(scenario, state, ProposedAction(action="accept_slot", slot_id="mon-1700"))
    assert result.accepted is False
    assert "not an available slot" in result.reason
    assert state.accepted_slot_id == ""


def test_naming_an_available_moment_takes_it_pending_confirmation(scenario):
    """The model may label "donderdag om tien uur is goed" as propose_slot; the code still takes the slot."""
    state = AppointmentState()
    apply_action(scenario, state, ProposedAction(action="state_reason", reason_text="Ik moet werken."))
    result = apply_action(scenario, state, ProposedAction(action="propose_slot", slot_id="thu-1000"))
    assert result.accepted and result.slot_id == "thu-1000"
    assert state.accepted_slot_id == "thu-1000" and not state.confirmed
    assert "accept_slot" in state.actions
    assert apply_action(scenario, state, ProposedAction(action="confirm")).accepted
    assert required_actions_completed(state, ["state_reason", "accept_slot", "confirm"])


def test_rejected_past_proposal_has_no_side_effects(scenario):
    state = AppointmentState(reason_stated=True, actions=["state_reason"])
    before = state.as_dict()
    result = apply_action(scenario, state, ProposedAction(action="propose_slot", slot_id="thu-1000"),
                          now=datetime(2026, 10, 1))
    assert not result.accepted and "past" in result.reason
    assert state.as_dict() == result.state == before
