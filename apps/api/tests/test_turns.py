"""The conversation turn: workflow guards, the HTTP endpoints, idempotency, restrictions and usage accounting."""

from __future__ import annotations

import io
import shutil
import wave

import pytest

from dlp.domains.content.service import MISSIONS_DIR, read_mission_file
from dlp.domains.practice.workflow import run_turn
from dlp.providers.fixtures import FixtureChatModel
from dlp.providers.registry import get_providers
from tests.conftest import FIXTURES, auth_headers

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
MISSION = {"mission_id": "appointment-change", "variant": "base"}


@pytest.fixture(scope="module")
def document():
    return read_mission_file(MISSIONS_DIR / "appointment-change" / "mission.json")


# --- workflow -------------------------------------------------------------------------------------------------------


def test_workflow_lets_the_code_decide_and_anchors_the_reply(document):
    scenario = document.scenario("dentist-base")
    chat = FixtureChatModel()
    state = run_turn(chat, scenario=scenario, appointment={}, history=[], learner_text="Ik moet werken.", request_id="w1")
    assert state["proposed"]["action"] == "state_reason"
    assert state["action_result"]["accepted"] is True
    assert state["appointment"]["reason_stated"] is True
    assert state["phase"] == "offer_slots"
    # the fixture leaves the offer to the fixed line, which names only the authoritative slots
    assert state["reply_source"] == "fixed_line"
    assert "donderdag om 10 uur" in state["reply_nl"]
    assert [c["step"] for c in state["model_calls"]] == ["propose_action", "compose_reply"]
    assert all(c["prompt_version"] for c in state["model_calls"])


def test_workflow_refuses_an_invented_slot_and_never_announces_it(document):
    scenario = document.scenario("dentist-base")
    chat = FixtureChatModel(replies={
        "propose-action-v1": {"action": "accept_slot", "slot_id": "sun-0300", "confidence": 0.9},
        "character-reply-v1": {"reply_nl": "Genoteerd, uw nieuwe afspraak staat vast op zondag om 3 uur."},
    })
    appointment = {"reason_stated": True, "actions": ["state_reason"]}
    state = run_turn(chat, scenario=scenario, appointment=appointment, history=[], learner_text="Zondag om drie uur.",
                     request_id="w2")
    assert state["action_result"]["accepted"] is False
    assert state["appointment"]["accepted_slot_id"] == ""
    # the model announced a booking the code refused: the fixed line for the phase is used instead
    assert state["reply_source"] == "fixed_line"
    assert "zondag" not in state["reply_nl"].lower()


def test_workflow_never_closes_the_call_before_the_code_did(document):
    """Seen on the laptop: the model said "Tot dan! Tot donderdag om tien uur dan." while nothing was accepted."""
    scenario = document.scenario("dentist-base")
    chat = FixtureChatModel(replies={
        "propose-action-v1": {"action": "confirm", "confidence": 0.9},
        "character-reply-v1": {"reply_nl": "Tot dan! Tot donderdag om tien uur dan."},
    })
    appointment = {"reason_stated": True, "actions": ["state_reason"]}
    state = run_turn(chat, scenario=scenario, appointment=appointment, history=[], learner_text="Ja, dat is goed. Tot dan!",
                     request_id="w5")
    assert state["action_result"]["accepted"] is False
    assert state["reply_source"] == "fixed_line"
    assert "donderdag om 10 uur" in state["reply_nl"], "the phase's fixed line offers the slots again"

    # accepted but not confirmed: a closing line is replaced by the confirmation question
    chat = FixtureChatModel(replies={
        "propose-action-v1": {"action": "accept_slot", "slot_id": "thu-1000", "confidence": 0.9},
        "character-reply-v1": {"reply_nl": "Prima, tot dan!"},
    })
    state = run_turn(chat, scenario=scenario, appointment=appointment, history=[], learner_text="Donderdag om tien uur.",
                     request_id="w6")
    assert state["appointment"]["accepted_slot_id"] == "thu-1000"
    assert state["reply_source"] == "fixed_line" and "Past dat?" in state["reply_nl"]


def test_workflow_uses_the_fixed_line_when_the_reply_call_fails(document):
    scenario = document.scenario("dentist-base")
    chat = FixtureChatModel(fail_calls=(2,))
    state = run_turn(chat, scenario=scenario, appointment={}, history=[], learner_text="Ik moet werken.", request_id="w3")
    assert state["action_result"]["accepted"] is True, "the proposal was read and validated"
    assert state["reply_source"] == "fixed_line"
    assert "donderdag om 10 uur" in state["reply_nl"]
    assert state["errors"] == ["compose_reply: injected fixture failure"]


def test_workflow_fails_when_the_model_cannot_read_the_utterance(document):
    """No fixed-line answer without the model's reading: that would simulate a conversation and burn turns."""
    from dlp.providers.base import ProviderError

    scenario = document.scenario("dentist-base")
    with pytest.raises(ProviderError):
        run_turn(FixtureChatModel(fail_first=1), scenario=scenario, appointment={}, history=[],
                 learner_text="Ik moet werken.", request_id="w4")


# --- endpoints ------------------------------------------------------------------------------------------------------


def _start(client, request_id="turn-start-0001", variant="base"):
    response = client.post("/practice/sessions", headers=auth_headers(request_id), json={**MISSION, "variant": variant})
    assert response.status_code == 201, response.text
    return response.json()["session"]["id"]


def _say(client, session_id, request_id, text, step_key="speak-call"):
    return client.post(f"/practice/sessions/{session_id}/turns", headers=auth_headers(request_id),
                       json={"step_key": step_key, "text": text})


def test_typed_turns_complete_the_speaking_step_with_evidence_and_usage(client):
    session_id = _start(client)

    first = _say(client, session_id, "turn-0001", "Goeiedag, ik wil mijn afspraak verzetten. Ik moet werken.")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["turn"]["modality"] == "typed"
    assert body["turn"]["proposed_action"]["action"] == "state_reason"
    assert body["turn"]["action_result"]["accepted"] is True
    assert body["appointment"]["reason_stated"] is True and body["step_completed"] is False
    assert body["turn"]["character_text"]
    assert body["turn"]["character_audio_asset_id"], "the reply is synthesised"
    assert body["turn"]["model_calls"][0]["prompt_version"] == "propose-action-v1"

    second = _say(client, session_id, "turn-0002", "Donderdag om tien uur is goed.").json()
    assert second["appointment"]["accepted_slot_id"] == "thu-1000"
    assert "donderdag 24 september om 10 uur" in second["turn"]["character_text"]

    third = _say(client, session_id, "turn-0003", "Ja, dat past. Tot dan!").json()
    assert third["appointment"]["confirmed"] is True
    assert third["step_completed"] is True
    assert third["session"]["status"] == "active", "the base speaking step does not close the session"
    assert third["session"]["step_progress"]["speak-call"] == {"turns": 3, "completed": True, "modalities": ["typed"]}

    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("turn-view")).json()
    assert [t["turn_index"] for t in view["turns"]] == [1, 2, 3]
    kinds = sorted(e["kind"] for e in view["evidence"])
    assert kinds == ["action_result"] * 3 + ["typed_text"] * 3
    typed = [e for e in view["evidence"] if e["kind"] == "typed_text"]
    assert all(e["modality"] == "typed" and e["source"] == "learner" and e["turn_id"] for e in typed)
    assert all(e["skill"] == "speaking" for e in view["evidence"])

    records = client.get("/progress", headers=auth_headers("turn-progress")).json()["skill_records"]
    speaking = next(r for r in records if r["skill"] == "speaking")
    assert speaking["status"] == "in_progress" and speaking["attempts"] == 1, "typed turns never count as speaking practice"
    assert speaking["latest_assessment"]["speak-call"] == {**speaking["latest_assessment"]["speak-call"],
                                                           "completed": True, "typed_only": True, "spoken": False}
    assert len(speaking["evidence_ids"]) == 6

    usage = client.get("/usage", headers=auth_headers("turn-usage")).json()["counters"]
    assert usage["model_calls"]["daily"]["used"] == 6 and usage["model_calls"]["daily"]["reserved"] == 0
    assert usage["tokens"]["daily"]["used"] > 0 and usage["tokens"]["daily"]["reserved"] == 0
    assert usage["audio_seconds"]["daily"]["used"] > 0, "character audio is counted"


def test_character_audio_is_served_and_labelled(client):
    session_id = _start(client)
    turn = _say(client, session_id, "audio-0001", "Ik ben ziek.").json()["turn"]
    response = client.get(f"/practice/sessions/{session_id}/turns/{turn['id']}/audio", headers=auth_headers("audio-get"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["x-audio-label"] == "synthetic-development"
    with wave.open(io.BytesIO(response.content), "rb") as handle:
        assert handle.getframerate() == 16000 and handle.getnframes() > 0
    other = client.get(f"/practice/sessions/{session_id}/turns/{turn['id']}/audio",
                       headers=auth_headers("audio-other", email="second@example.com"))
    assert other.status_code == 404


def test_a_retry_with_the_same_request_id_returns_the_same_turn(client):
    session_id = _start(client)
    first = _say(client, session_id, "same-0001", "Ik heb een examen.").json()
    again = _say(client, session_id, "same-0001", "Ik heb een examen.").json()
    assert again["deduplicated"] is True and first["deduplicated"] is False
    assert again["turn"]["id"] == first["turn"]["id"]
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("same-view")).json()
    assert len(view["turns"]) == 1
    usage = client.get("/usage", headers=auth_headers("same-usage")).json()["counters"]["model_calls"]["daily"]
    assert usage["used"] == 2


def test_a_model_failure_keeps_the_failed_turn_and_releases_usage(client, monkeypatch):
    session_id = _start(client)
    monkeypatch.setattr("dlp.domains.practice.workflow.build_graph", lambda chat: _Exploding())
    response = _say(client, session_id, "fail-0001", "Ik moet werken.")
    assert response.status_code == 502
    assert "model endpoint unreachable" in response.json()["detail"]
    assert response.json()["turn"]["status"] == "failed"
    assert response.json()["turn"]["error"].startswith("RuntimeError")
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("fail-view")).json()
    assert [t["status"] for t in view["turns"]] == ["failed"]
    assert view["evidence"] == []
    usage = client.get("/usage", headers=auth_headers("fail-usage")).json()["counters"]
    assert usage["model_calls"]["daily"] == {**usage["model_calls"]["daily"], "used": 0, "reserved": 0}
    assert usage["tokens"]["daily"]["reserved"] == 0
    # the same request id repeats the failure; a new one starts a new turn
    assert _say(client, session_id, "fail-0001", "Ik moet werken.").status_code == 502
    monkeypatch.undo()
    ok = _say(client, session_id, "fail-0002", "Ik moet werken.").json()
    assert ok["turn"]["turn_index"] == 2
    assert ok["session"]["step_progress"]["speak-call"]["turns"] == 1, "a failed turn does not use up the budget"


def test_an_unreachable_model_fails_the_turn_instead_of_pretending(client, monkeypatch):
    session_id = _start(client)
    providers = get_providers()
    monkeypatch.setattr(providers, "chat", FixtureChatModel(fail_first=1))
    response = _say(client, session_id, "down-0001", "Ik moet werken.")
    assert response.status_code == 502
    assert "injected fixture failure" in response.json()["detail"]
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("down-view")).json()
    assert view["turns"][0]["status"] == "failed" and view["evidence"] == []
    assert view["session"]["appointment"] == {}


class _Exploding:
    def invoke(self, state):
        raise RuntimeError("model endpoint unreachable")


def test_turn_restrictions(client):
    session_id = _start(client)
    assert _say(client, session_id, "restrict-0001", "Hallo", step_key="read-reminder").status_code == 400
    assert _say(client, session_id, "restrict-0002", "Hallo", step_key="nope").status_code == 404
    assert _say(client, session_id, "restrict-0003", "Hallo", step_key="checkpoint-transfer").status_code == 409
    assert _say(client, session_id, "restrict-0004", "   ").status_code == 422

    transfer_id = _start(client, "turn-start-transfer", variant="transfer")
    typed = _say(client, transfer_id, "restrict-0005", "Ik moet werken.", step_key="checkpoint-transfer")
    assert typed.status_code == 403, "the checkpoint takes speech only"


def test_max_turns_closes_the_step(client, monkeypatch):
    from dlp.domains.practice import turns as turns_module

    session_id = _start(client)
    original = turns_module.turn_count_for
    monkeypatch.setattr(turns_module, "turn_count_for", lambda s, p, k: original(s, p, k) + 10)  # max_turns is 12
    assert _say(client, session_id, "maxturn-0001", "Hallo.").status_code == 200
    assert _say(client, session_id, "maxturn-0002", "Hallo?").status_code == 200
    assert _say(client, session_id, "maxturn-0003", "Hallo!").status_code == 409


def test_the_transfer_checkpoint_allows_exactly_one_attempt(client):
    transfer_id = _start(client, "cp-start-0001", variant="transfer")
    resumed = client.post("/practice/sessions", headers=auth_headers("cp-start-0002"), json={**MISSION, "variant": "transfer"})
    assert resumed.json()["session"]["id"] == transfer_id
    closed = client.post(f"/practice/sessions/{transfer_id}/abandon", headers=auth_headers("cp-abandon-01"))
    assert closed.status_code == 200
    again = client.post("/practice/sessions", headers=auth_headers("cp-start-0003"), json={**MISSION, "variant": "transfer"})
    assert again.status_code == 409
    assert "no retry" in again.json()["detail"]


@needs_ffmpeg
def test_a_spoken_turn_records_the_transcript_as_evidence(client):
    session_id = _start(client)
    wav = (FIXTURES / "tone_1s.wav").read_bytes()
    response = client.post(
        f"/practice/sessions/{session_id}/turns/speech", headers=auth_headers("speech-turn-0001"),
        files={"audio": ("turn.wav", wav, "audio/wav")}, data={"step_key": "speak-call"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["turn"]["modality"] == "speech"
    assert body["turn"]["learner_text"], "the transcript is the learner text"
    assert body["turn"]["learner_audio_asset_id"]
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("speech-view")).json()
    transcript = next(e for e in view["evidence"] if e["kind"] == "transcript")
    assert transcript["modality"] == "speech" and transcript["source"] == "fixture"
    assert transcript["payload"]["stt"]["provider"] == "fixture"
    assert transcript["payload"]["audio_asset_id"] == body["turn"]["learner_audio_asset_id"]
    # a spoken turn makes the step count as speaking practice once the goal is reached
    for request_id, text in (("speech-typed-1", "Ik moet werken."), ("speech-typed-2", "Donderdag om tien uur is goed."),
                             ("speech-typed-3", "Ja, dat past. Tot dan!")):
        assert _say(client, session_id, request_id, text).status_code == 200
    records = client.get("/progress", headers=auth_headers("speech-progress")).json()["skill_records"]
    speaking = next(r for r in records if r["skill"] == "speaking")
    assert speaking["status"] == "practised" and speaking["latest_assessment"]["speak-call"]["spoken"] is True
    providers = get_providers()
    assert providers.blob.exists(f"recordings/{_learner_id(client)}/speech-turn-0001.wav")

    # the checkpoint refuses no spoken turn, and a repeated upload with the same request id is answered from the stored turn
    again = client.post(
        f"/practice/sessions/{session_id}/turns/speech", headers=auth_headers("speech-turn-0001"),
        files={"audio": ("turn.wav", wav, "audio/wav")}, data={"step_key": "speak-call"},
    )
    assert again.status_code == 200 and again.json()["deduplicated"] is True
    turns = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("speech-view-2")).json()["turns"]
    assert len(turns) == 4, "the repeated upload added no turn"


def _learner_id(client) -> str:
    return client.get("/progress", headers=auth_headers("who-am-i-01")).json()["learner"]["id"]
