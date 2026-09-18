"""Evidence for reading, listening and writing, the help ladder, feedback grounded in evidence, the export."""

from __future__ import annotations

import io
import wave

from tests.conftest import auth_headers

MISSION = {"mission_id": "appointment-change", "variant": "base"}


def _start(client, request_id="steps-start-0001", variant="base"):
    response = client.post("/practice/sessions", headers=auth_headers(request_id), json={**MISSION, "variant": variant})
    assert response.status_code == 201, response.text
    return response.json()["session"]["id"]


def _answer(client, session_id, request_id, step_key, question_id, chosen):
    return client.post(f"/practice/sessions/{session_id}/answers", headers=auth_headers(request_id),
                       json={"step_key": step_key, "question_id": question_id, "chosen_index": chosen})


def test_reading_answers_are_judged_on_the_server_and_recorded(client):
    session_id = _start(client)
    wrong = _answer(client, session_id, "answer-0001", "read-reminder", "q-when", 1).json()
    assert wrong["correct"] is False and wrong["answer_index"] == 0 and wrong["step_completed"] is False
    assert wrong["evidence"]["kind"] == "answer" and wrong["evidence"]["payload"]["attempt"] == 1

    right = _answer(client, session_id, "answer-0002", "read-reminder", "q-when", 0).json()
    assert right["correct"] is True and right["evidence"]["payload"]["attempt"] == 2
    second = _answer(client, session_id, "answer-0003", "read-reminder", "q-cannot-come", 1).json()
    assert second["step_completed"] is True
    assert second["session"]["step_progress"]["read-reminder"] == {
        **second["session"]["step_progress"]["read-reminder"], "completed": True, "correct": 2, "total": 2,
    }

    records = client.get("/progress", headers=auth_headers("answer-progress")).json()["skill_records"]
    reading = next(r for r in records if r["skill"] == "reading")
    assert reading["status"] == "practised" and len(reading["evidence_ids"]) == 3
    assert reading["latest_assessment"]["read-reminder"]["correct"] == 2

    assert _answer(client, session_id, "answer-0004", "read-reminder", "q-nope", 0).status_code == 404
    assert _answer(client, session_id, "answer-0005", "read-reminder", "q-when", 7).status_code == 422
    assert _answer(client, session_id, "answer-0006", "speak-call", "q-when", 0).status_code == 400


def test_help_use_is_evidence_and_refused_in_the_checkpoint(client):
    session_id = _start(client)
    response = client.post(f"/practice/sessions/{session_id}/help", headers=auth_headers("help-0001"),
                           json={"step_key": "read-reminder", "level": 2, "kind": "gloss_fa"})
    assert response.status_code == 200
    assert response.json()["evidence"]["kind"] == "help_used"
    assert response.json()["session"]["step_progress"]["read-reminder"]["help_levels"] == [2]

    transfer_id = _start(client, "help-start-transfer", variant="transfer")
    refused = client.post(f"/practice/sessions/{transfer_id}/help", headers=auth_headers("help-0002"),
                          json={"step_key": "checkpoint-transfer", "level": 1, "kind": "hint_nl"})
    assert refused.status_code == 403


def test_writing_draft_autosaves_and_the_submission_is_typed_evidence(client):
    session_id = _start(client)
    draft = client.put(f"/practice/sessions/{session_id}/drafts/write-message", headers=auth_headers("draft-0001"),
                       json={"text": "Beste tandarts, ik kan"})
    assert draft.status_code == 200 and draft.json()["draft"]["word_count"] == 4
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("draft-view")).json()
    assert view["drafts"]["write-message"]["text"] == "Beste tandarts, ik kan"
    assert view["evidence"] == [], "a draft is not evidence"

    short = client.post(f"/practice/sessions/{session_id}/writing", headers=auth_headers("write-0001"),
                        json={"step_key": "write-message", "text": "Ik kan niet komen."})
    assert short.status_code == 422 and "at least 25" in short.json()["detail"]

    message = ("Beste tandarts De Smet, ik kan woensdag niet komen naar de praktijk omdat ik moet werken. "
               "Kan ik een nieuwe afspraak maken op donderdag of vrijdag? Bedankt en tot binnenkort. Groeten, Mahmoud")
    submitted = client.post(f"/practice/sessions/{session_id}/writing", headers=auth_headers("write-0002"),
                            json={"step_key": "write-message", "text": message})
    assert submitted.status_code == 200, submitted.text
    body = submitted.json()
    assert body["evidence"]["kind"] == "typed_text" and body["evidence"]["modality"] == "typed"
    assert body["missing"] == [] and 25 <= body["word_count"] <= 80 and body["step_completed"] is True
    records = client.get("/progress", headers=auth_headers("write-progress")).json()["skill_records"]
    assert next(r for r in records if r["skill"] == "writing")["status"] == "practised"


def test_listening_audio_is_synthesised_once_and_labelled(client):
    key = "fixed/appointment-change/voicemail-base.wav"
    first = client.get(f"/missions/appointment-change/audio/{key}", headers=auth_headers("audio-fixed-01"))
    assert first.status_code == 200 and first.headers["content-type"] == "audio/wav"
    assert first.headers["x-audio-label"] == "synthetic-development"
    with wave.open(io.BytesIO(first.content), "rb") as handle:
        assert handle.getframerate() == 16000
    def used_seconds(request_id: str) -> float:
        return client.get("/usage", headers=auth_headers(request_id)).json()["counters"]["audio_seconds"]["daily"]["used"]

    usage_after_first = used_seconds("audio-usage-1")
    again = client.get(f"/missions/appointment-change/audio/{key}", headers=auth_headers("audio-fixed-02"))
    assert again.content == first.content
    assert used_seconds("audio-usage-2") == usage_after_first, "the stored file is served without a second synthesis"
    missing = client.get("/missions/appointment-change/audio/fixed/nope.wav", headers=auth_headers("audio-fixed-03"))
    assert missing.status_code == 404


def test_feedback_cites_only_real_evidence(client):
    session_id = _start(client)
    too_early = client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-0000"),
                            json={"step_key": "read-reminder"})
    assert too_early.status_code == 409 and "not enough evidence" in too_early.json()["detail"]

    _answer(client, session_id, "fb-answer-1", "read-reminder", "q-when", 0)
    _answer(client, session_id, "fb-answer-2", "read-reminder", "q-cannot-come", 0)
    response = client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-0001"),
                           json={"step_key": "read-reminder"})
    assert response.status_code == 200, response.text
    report = response.json()["report"]
    assert report["skill"] == "reading" and report["prompt_version"] == "feedback-v1"
    assert report["summary_nl"] and report["summary_fa"]
    assert [p["kind"] for p in report["points"]] == ["strength", "suggestion"], "the point citing E99 was dropped"
    assert report["dropped_points"] == 1
    view = client.get(f"/practice/sessions/{session_id}", headers=auth_headers("feedback-view")).json()
    real_ids = {e["id"] for e in view["evidence"]}
    for point in report["points"]:
        assert point["evidence_ids"] and set(point["evidence_ids"]) <= real_ids
    assert set(report["evidence_ids"]) == real_ids

    again = client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-0001"),
                        json={"step_key": "read-reminder"})
    assert again.json()["report"]["id"] == report["id"], "same request id, same report"
    listed = client.get(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-list")).json()["reports"]
    assert len(listed) == 1 and view["feedback"][0]["id"] == report["id"]
    usage = client.get("/usage", headers=auth_headers("feedback-usage")).json()["counters"]["model_calls"]["daily"]
    assert usage["used"] == 1 and usage["reserved"] == 0


def test_speaking_feedback_needs_a_code_validated_action(client):
    session_id = _start(client)
    client.post(f"/practice/sessions/{session_id}/turns", headers=auth_headers("fb-turn-1"),
                json={"step_key": "speak-call", "text": "Goeiedag."})
    client.post(f"/practice/sessions/{session_id}/turns", headers=auth_headers("fb-turn-2"),
                json={"step_key": "speak-call", "text": "Hallo?"})
    early = client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-sp-0"),
                        json={"step_key": "speak-call"})
    assert early.status_code == 409 and "code-validated action" in early.json()["detail"]
    client.post(f"/practice/sessions/{session_id}/turns", headers=auth_headers("fb-turn-3"),
                json={"step_key": "speak-call", "text": "Ik moet werken."})
    ok = client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("feedback-sp-1"),
                     json={"step_key": "speak-call"})
    assert ok.status_code == 200 and ok.json()["report"]["skill"] == "speaking"


def test_export_is_complete_and_owner_only(client):
    session_id = _start(client)
    _answer(client, session_id, "export-answer", "read-reminder", "q-when", 0)
    response = client.get("/export", headers=auth_headers("export-0001"))
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith('attachment; filename="learner-export-')
    body = response.json()
    assert body["learner"]["email"] == "owner@example.com"
    assert {r["skill"] for r in body["skill_records"]} == {"listening", "reading", "speaking", "writing"}
    exported = next(s for s in body["sessions"] if s["id"] == session_id)
    assert [e["kind"] for e in exported["evidence"]] == ["answer"] and exported["feedback"] == []
    assert "counters" in body["usage"]
