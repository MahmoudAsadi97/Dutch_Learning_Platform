"""Appointment actions are validated here, in code, never by the model.

The model may *propose* an action (for example "the learner accepted slot X").
Only this module decides whether the commitment is valid against the scenario's
authoritative slots and the session's current state, and the character may only
announce acceptance after `apply_action` succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field

from dlp.domains.content.schemas import Scenario

ActionType = Literal["state_reason", "propose_slot", "accept_slot", "ask_repeat", "confirm", "cancel", "none"]


class ProposedAction(BaseModel):
    """Structured output the model must produce for every learner turn."""

    action: ActionType = "none"
    reason_text: str = ""
    slot_id: str = ""
    proposed_day: date | None = None
    proposed_time: time | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


@dataclass
class AppointmentState:
    reason_stated: bool = False
    offered_slot_ids: list[str] = field(default_factory=list)
    accepted_slot_id: str = ""
    confirmed: bool = False
    cancelled: bool = False
    actions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "reason_stated": self.reason_stated,
            "offered_slot_ids": list(self.offered_slot_ids),
            "accepted_slot_id": self.accepted_slot_id,
            "confirmed": self.confirmed,
            "cancelled": self.cancelled,
            "actions": list(self.actions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AppointmentState:
        data = data or {}
        return cls(
            reason_stated=bool(data.get("reason_stated", False)),
            offered_slot_ids=list(data.get("offered_slot_ids", [])),
            accepted_slot_id=str(data.get("accepted_slot_id", "")),
            confirmed=bool(data.get("confirmed", False)),
            cancelled=bool(data.get("cancelled", False)),
            actions=list(data.get("actions", [])),
        )


@dataclass(frozen=True)
class ActionResult:
    accepted: bool
    action: str
    reason: str
    state: dict[str, Any]
    slot_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "action": self.action, "reason": self.reason,
                "slot_id": self.slot_id, "state": self.state}


def _slot_matches(scenario: Scenario, proposed: ProposedAction) -> str:
    """Resolve a proposed slot to an authoritative slot id, by id or by day and start time."""
    for slot in scenario.available_slots:
        if proposed.slot_id and slot.id == proposed.slot_id:
            return slot.id
        if proposed.proposed_day == slot.day and proposed.proposed_time == slot.start:
            return slot.id
    return ""


def apply_action(scenario: Scenario, state: AppointmentState, proposed: ProposedAction,
                 now: datetime | None = None) -> ActionResult:
    action = proposed.action
    if action == "none":
        return ActionResult(False, action, "no action proposed", state.as_dict())
    if action not in scenario.allowed_actions:
        return ActionResult(False, action, f"action {action} is not allowed in scenario {scenario.id}", state.as_dict())
    if state.cancelled:
        return ActionResult(False, action, "the appointment was cancelled; nothing further can be done", state.as_dict())

    if action == "state_reason":
        if not proposed.reason_text.strip():
            return ActionResult(False, action, "no reason text", state.as_dict())
        state.reason_stated = True
        state.actions.append(action)
        return ActionResult(True, action, "reason recorded", state.as_dict())

    if action == "ask_repeat":
        state.actions.append(action)
        return ActionResult(True, action, "repeat requested", state.as_dict())

    if action == "propose_slot":
        slot_id = _slot_matches(scenario, proposed)
        if not slot_id:
            return ActionResult(False, action, "the proposed moment is not an available slot", state.as_dict())
        # A learner who names one of the available moments has chosen it: the model may label that
        # "propose" or "accept", the outcome is the same — the slot is taken, confirmation pending.
        slot = next(s for s in scenario.available_slots if s.id == slot_id)
        reference = (now or datetime.combine(scenario.reference_date, time(0, 0))).date()
        if slot.day < reference:
            return ActionResult(False, action, "the slot lies in the past", state.as_dict())
        if slot_id not in state.offered_slot_ids:
            state.offered_slot_ids.append(slot_id)
        state.actions.append(action)
        state.accepted_slot_id = slot_id
        state.confirmed = False
        state.actions.append("accept_slot")
        return ActionResult(True, action, "slot is available and taken, confirmation pending", state.as_dict(),
                            slot_id=slot_id)

    if action == "accept_slot":
        slot_id = _slot_matches(scenario, proposed)
        if not slot_id:
            return ActionResult(False, action, "the accepted moment is not an available slot", state.as_dict())
        if state.offered_slot_ids and slot_id not in state.offered_slot_ids:
            return ActionResult(False, action, "the slot was never offered in this conversation", state.as_dict())
        slot = next(s for s in scenario.available_slots if s.id == slot_id)
        reference = (now or datetime.combine(scenario.reference_date, time(0, 0))).date()
        if slot.day < reference:
            return ActionResult(False, action, "the slot lies in the past", state.as_dict())
        state.accepted_slot_id = slot_id
        state.confirmed = False
        state.actions.append(action)
        return ActionResult(True, action, "slot accepted, confirmation pending", state.as_dict(), slot_id=slot_id)

    if action == "confirm":
        if not state.accepted_slot_id:
            return ActionResult(False, action, "nothing to confirm: no slot accepted yet", state.as_dict())
        state.confirmed = True
        state.actions.append(action)
        return ActionResult(True, action, "new appointment confirmed", state.as_dict(), slot_id=state.accepted_slot_id)

    if action == "cancel":
        state.cancelled = True
        state.actions.append(action)
        return ActionResult(True, action, "appointment cancelled", state.as_dict())

    return ActionResult(False, action, "unknown action", state.as_dict())


def required_actions_completed(state: AppointmentState, required: list[str]) -> bool:
    done = set(state.actions)
    if "confirm" in required and not state.confirmed:
        return False
    return all(item in done for item in required)
