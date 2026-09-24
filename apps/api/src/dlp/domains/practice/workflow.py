"""The practice turn as a small LangGraph workflow with typed state.

    propose_action (model, structured)  →  validate_action (code, authoritative)  →  compose_reply (model, structured)

The model only proposes; `apply_action` decides. The reply is anchored on the scenario's fixed
line for the current phase, and the fixed line itself is used when the reply call fails or contradicts
the decision, so the character never announces something the code did not accept.

A failure of the *first* call is not softened: without the model's reading of the utterance no action
can be recognised, so a fixed-line answer would only simulate a conversation and, in the checkpoint,
burn the learner's single attempt. The error propagates and the turn is recorded as failed.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from dlp.domains.content.schemas import Scenario
from dlp.domains.practice.actions import ActionResult, AppointmentState, ProposedAction, apply_action
from dlp.domains.practice.prompts import (
    CHARACTER_REPLY_VERSION,
    PROPOSE_ACTION_VERSION,
    CharacterReply,
    ProposedActionReply,
    character_reply_messages,
    fixed_line,
    phase_for,
    propose_action_messages,
)
from dlp.providers.base import ChatMessage, ChatModel, ProviderError


class TurnState(TypedDict, total=False):
    # inputs
    scenario: Scenario
    appointment: dict[str, Any]
    history: list[tuple[str, str]]
    learner_text: str
    request_id: str
    max_output_tokens: int
    # produced
    proposed: dict[str, Any]
    action_result: dict[str, Any]
    phase: str
    anchor: str
    reply_nl: str
    reply_source: str  # model | fixed_line
    model_calls: list[dict[str, Any]]
    errors: list[str]


def _record(state: TurnState, call: dict[str, Any]) -> list[dict[str, Any]]:
    return [*state.get("model_calls", []), call]


def build_graph(chat: ChatModel):
    def propose_action(state: TurnState) -> dict[str, Any]:
        scenario = state["scenario"]
        appointment = AppointmentState.from_dict(state.get("appointment"))
        messages = [ChatMessage(role, text) for role, text in  # type: ignore[arg-type]
                    propose_action_messages(scenario, appointment, state.get("history", []), state["learner_text"])]
        # A ProviderError here propagates: see the module docstring.
        result = chat.complete(messages, schema=ProposedActionReply, max_output_tokens=state.get("max_output_tokens", 200),
                               temperature=0.0, prompt_version=PROPOSE_ACTION_VERSION, request_id=state.get("request_id", ""))
        parsed = result.parsed if isinstance(result.parsed, ProposedActionReply) else ProposedActionReply(action="none")
        proposed = ProposedAction(action=parsed.action, reason_text=parsed.reason_text, slot_id=parsed.slot_id,
                                  choice_id=parsed.choice_id, confidence=parsed.confidence)
        call = {"step": "propose_action", "prompt_version": result.prompt_version, "provider": result.provider,
                "model": result.model, "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                "latency_ms": result.latency_ms, "attempts": result.attempts, "understood_nl": parsed.understood_nl}
        return {"proposed": proposed.model_dump(mode="json"), "model_calls": _record(state, call)}

    def validate_action(state: TurnState) -> dict[str, Any]:
        scenario = state["scenario"]
        appointment = AppointmentState.from_dict(state.get("appointment"))
        proposed = ProposedAction.model_validate(state["proposed"])
        result: ActionResult = apply_action(scenario, appointment, proposed)
        phase = phase_for(appointment, scenario)
        return {"action_result": result.as_dict(), "appointment": appointment.as_dict(), "phase": phase,
                "anchor": fixed_line(scenario, phase, appointment)}

    def compose_reply(state: TurnState) -> dict[str, Any]:
        scenario = state["scenario"]
        appointment = AppointmentState.from_dict(state.get("appointment"))
        result = state["action_result"]
        anchor = state["anchor"]
        if scenario.kind == "service":
            # Prices, routes and remedies must come from authored facts, not generated promises.
            if appointment.cancelled:
                return {"reply_nl": "Het gesprek is geannuleerd. Er is niets afgesproken.", "reply_source": "fixed_line"}
            if result["action"] == "ask_repeat":
                anchor = fixed_line(scenario, "repeat", appointment) + " " + anchor
            elif not result["accepted"] and result["action"] != "none":
                anchor = fixed_line(scenario, "clarify", appointment) + " " + anchor
            return {"reply_nl": anchor, "reply_source": "fixed_line"}
        if result["accepted"]:
            note = f"actie {result['action']} aanvaard ({result['reason']})"
        else:
            note = (f"actie {result['action']} NIET aanvaard ({result['reason']}); "
                    "vraag vriendelijk om verduidelijking of herhaal het aanbod")
        messages = [ChatMessage(role, text) for role, text in  # type: ignore[arg-type]
                    character_reply_messages(scenario, appointment, state.get("history", []), state["learner_text"],
                                             state["phase"], anchor, note)]
        try:
            outcome = chat.complete(messages, schema=CharacterReply, max_output_tokens=state.get("max_output_tokens", 200),
                                    temperature=0.3, prompt_version=CHARACTER_REPLY_VERSION,
                                    request_id=state.get("request_id", ""))
        except ProviderError as exc:
            return {"reply_nl": anchor or "Sorry, kunt u dat herhalen?", "reply_source": "fixed_line",
                    "errors": [*state.get("errors", []), f"compose_reply: {exc}"]}
        reply = outcome.parsed.reply_nl.strip() if isinstance(outcome.parsed, CharacterReply) else ""
        call = {"step": "compose_reply", "prompt_version": outcome.prompt_version, "provider": outcome.provider,
                "model": outcome.model, "input_tokens": outcome.input_tokens, "output_tokens": outcome.output_tokens,
                "latency_ms": outcome.latency_ms, "attempts": outcome.attempts}
        if not reply or _contradicts_decision(reply, state, appointment):
            return {"reply_nl": anchor or reply, "reply_source": "fixed_line", "model_calls": _record(state, call)}
        return {"reply_nl": reply, "reply_source": "model", "model_calls": _record(state, call)}

    graph = StateGraph(TurnState)
    graph.add_node("propose_action", propose_action)
    graph.add_node("validate_action", validate_action)
    graph.add_node("compose_reply", compose_reply)
    graph.add_edge(START, "propose_action")
    graph.add_edge("propose_action", "validate_action")
    graph.add_edge("validate_action", "compose_reply")
    graph.add_edge("compose_reply", END)
    return graph.compile()


CONFIRMATION_WORDS = ("genoteerd", "staat vast", "is bevestigd", "ik zet u op", "ik zet je op",
                      "uw nieuwe afspraak", "je nieuwe afspraak", "verzet naar", "verplaatst naar", "ingepland",
                      "staat nu op", "zie u dan", "zie je dan", "tot dan", "tot donderdag", "tot vrijdag",
                      "tot maandag", "tot dinsdag", "tot woensdag", "tot zaterdag", "tot zondag")


def _contradicts_decision(reply: str, state: TurnState, appointment: AppointmentState) -> bool:
    """A reply that announces or closes a booking while nothing was accepted contradicts the code's decision,
    and so does a closing line while the accepted slot is not confirmed yet."""
    lowered = reply.lower()
    announces = any(word in lowered for word in CONFIRMATION_WORDS)
    if not appointment.accepted_slot_id:
        return announces
    closes = any(word in lowered for word in ("tot dan", "zie u dan", "zie je dan", "fijne dag"))
    return closes and not appointment.confirmed


def run_turn(chat: ChatModel, *, scenario: Scenario, appointment: dict[str, Any], history: list[tuple[str, str]],
             learner_text: str, request_id: str, max_output_tokens: int = 200) -> TurnState:
    graph = build_graph(chat)
    return graph.invoke({
        "scenario": scenario, "appointment": appointment, "history": history, "learner_text": learner_text,
        "request_id": request_id, "max_output_tokens": max_output_tokens, "model_calls": [], "errors": [],
    })
