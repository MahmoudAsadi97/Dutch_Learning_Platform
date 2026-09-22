"""Prompt templates for the conversation turn. Every template carries a version tag that is stored with the turn."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from dlp.domains.content.schemas import Scenario
from dlp.domains.practice.actions import ActionType, AppointmentState

PROPOSE_ACTION_VERSION = "propose-action-v1"
CHARACTER_REPLY_VERSION = "character-reply-v1"

DAY_NAMES_NL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTH_NAMES_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
                  "september", "oktober", "november", "december"]


def format_day(day: date) -> str:
    return f"{DAY_NAMES_NL[day.weekday()]} {day.day} {MONTH_NAMES_NL[day.month - 1]}"


def format_time(value: time) -> str:
    return f"{value.hour}.{value.minute:02d} uur" if value.minute else f"{value.hour} uur"


def describe_slot(scenario: Scenario, slot_id: str) -> str:
    slot = next((s for s in scenario.available_slots if s.id == slot_id), None)
    if slot is None:
        return slot_id
    return f"{format_day(slot.day)} om {format_time(slot.start)}"


class ProposedActionReply(BaseModel):
    """What the model must return for `propose_action`: its reading of the learner's last utterance."""

    action: ActionType = Field(description="one of the allowed actions, or none")
    reason_text: str = Field(default="", description="the reason the learner gave, in their words, if action is state_reason")
    slot_id: str = Field(default="", description="the id of the slot the learner accepted or proposed, if any")
    understood_nl: str = Field(default="", description="one short Dutch sentence summarising what the learner said")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class CharacterReply(BaseModel):
    """What the model must return for `compose_reply`."""

    reply_nl: str = Field(description="the character's next line, one or two short sentences, in Dutch")


def phase_for(state: AppointmentState, scenario: Scenario) -> str:
    if state.cancelled:
        return "closing"
    if state.confirmed:
        return "closing"
    if state.accepted_slot_id:
        return "confirm"
    if state.reason_stated:
        return "offer_slots"
    return "ask_reason"


def fixed_line(scenario: Scenario, when: str, state: AppointmentState) -> str:
    for line in scenario.fixed_lines:
        if line.when == when:
            text = line.text.nl
            if "{slot}" in text:
                text = text.replace("{slot}", describe_slot(scenario, state.accepted_slot_id))
            return text
    return ""


def _slots_block(scenario: Scenario) -> str:
    return "\n".join(f"- id {slot.id}: {format_day(slot.day)} {format_time(slot.start)}" for slot in scenario.available_slots)


def propose_action_messages(scenario: Scenario, state: AppointmentState, history: list[tuple[str, str]],
                            learner_text: str) -> list[tuple[str, str]]:
    """(role, content) pairs. The model interprets; it never decides — the code validates the proposal."""
    system = (
        "Je analyseert wat een taalleerder (niveau A2) zegt in een telefoongesprek om een afspraak te verzetten. "
        "Je kiest de bedoeling van de leerder uit een vaste lijst. Je verzint geen tijdstippen.\n\n"
        f"Situatie: {scenario.setting.nl}\n"
        f"Huidige afspraak: {scenario.appointment.what.nl} bij {scenario.appointment.with_whom.nl} op "
        f"{format_day(scenario.appointment.day)} om {format_time(scenario.appointment.start)}.\n"
        f"Beschikbare nieuwe momenten:\n{_slots_block(scenario)}\n\n"
        f"Vandaag is {format_day(scenario.reference_date)}.\n\n"
        "Acties:\n"
        "- state_reason: de leerder zegt waarom hij/zij niet kan komen (reason_text = de reden)\n"
        "- accept_slot: de leerder noemt of aanvaardt een van de beschikbare momenten, bijvoorbeeld "
        "\"donderdag om tien uur is goed\" (slot_id verplicht)\n"
        "- propose_slot: de leerder stelt een moment voor dat NIET in de lijst staat (slot_id leeg)\n"
        "- ask_repeat: de leerder vraagt om te herhalen of begrijpt het niet\n"
        "- confirm: de leerder bevestigt de nieuwe afspraak (ja, dat is goed, tot dan)\n"
        "- cancel: de leerder wil de afspraak helemaal annuleren\n"
        "- none: iets anders (begroeting, smalltalk, onduidelijk)\n\n"
        f"Stand van zaken: reden gezegd = {state.reason_stated}, aanvaard moment = {state.accepted_slot_id or 'geen'}, "
        f"bevestigd = {state.confirmed}."
    )
    messages: list[tuple[str, str]] = [("system", system)]
    for role, text in history[-6:]:
        messages.append(("assistant" if role == "character" else "user", text))
    messages.append(("user", f"Laatste uiting van de leerder: \"{learner_text}\""))
    return messages


def character_reply_messages(scenario: Scenario, state: AppointmentState, history: list[tuple[str, str]],
                             learner_text: str, phase: str, anchor: str, action_note: str) -> list[tuple[str, str]]:
    register = "u-vorm (beleefd)" if scenario.character.register_style == "formal" else "je-vorm (informeel, vriendelijk)"
    system = (
        f"Je bent {scenario.character.name}, {scenario.character.role.nl}. Je spreekt Belgisch Standaardnederlands "
        f"op niveau A2: korte zinnen, gewone woorden, {register}. "
        "Je praat met een taalleerder die belt om een afspraak te verzetten.\n\n"
        f"Situatie: {scenario.setting.nl}\n"
        f"Vandaag is {format_day(scenario.reference_date)}.\n"
        f"Huidige afspraak: {format_day(scenario.appointment.day)} om {format_time(scenario.appointment.start)}.\n"
        f"Beschikbare momenten (alleen deze mag je aanbieden):\n{_slots_block(scenario)}\n\n"
        f"Fase van het gesprek: {phase}. Richtlijn voor deze fase: \"{anchor}\"\n"
        f"Wat de toepassing besliste over de laatste uiting: {action_note}\n\n"
        "Regels: bevestig nooit een afspraak die de toepassing niet aanvaard heeft en sluit het gesprek nooit af "
        "(geen \"tot dan\") zolang de nieuwe afspraak niet bevestigd is. Verzin geen andere momenten en geen andere "
        "dagen; zeg niet \"morgen\". Antwoord met één of twee korte zinnen. Geen uitleg, geen vertaling."
    )
    messages: list[tuple[str, str]] = [("system", system)]
    for role, text in history[-6:]:
        messages.append(("assistant" if role == "character" else "user", text))
    messages.append(("user", learner_text))
    return messages
