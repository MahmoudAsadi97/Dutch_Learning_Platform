"""Support is stored before playback and cannot become independent completion evidence."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from dlp.domains.exercises import service
from dlp.domains.exercises.schemas import ItemView
from tests.conftest import auth_headers
from tests.test_exercises_topic_completion import (
    _finish,
    _observations,
    _post,
    _questions,
    _read,
    _right,
    _run,
    _stage_skill,
    _topic,
    _topic_row,
)


def _support(client, view, item, headers=None):
    return client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/assistance",
                       headers=auth_headers() if headers is None else headers)


def _answer_questions(client, view, tag):
    for index, item in enumerate(_questions(view)):
        response = _post(client, view, item, "answer", f"{tag}-answer-{index}", answer=_right(item))
        assert response.status_code == 200, response.text


def test_reading_assistance_survives_reload_is_sticky_and_awards_no_false_completion(client):
    view = _topic(client, "assistance-reading-create").json()
    passage = view["items"][0]
    assert passage["hint_used"] is False
    first = _support(client, view, passage)
    second = _support(client, view, passage)
    assert first.status_code == second.status_code == 200
    assert first.json()["hint_used"] is second.json()["hint_used"] is True
    resumed = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    assert all(item["hint_used"] for item in resumed["items"])
    assert all(item["attempts_left"] > 0 and item["state"] == "open" for item in resumed["items"])
    assert resumed["progress"]["closed"] == 0
    # A stale client sends false: the server preserves the durable support flag.
    _read(client, resumed, "assisted-pass")
    _answer_questions(client, resumed, "assisted-pass")
    finished = _finish(client, resumed, "assisted-pass-finish")
    assert finished.status_code == 200, finished.text
    completion = finished.json()["summary"]["completion"]
    assert completion["counted"] is False and completion["reason"] == "assisted"
    assert completion["completed"] is False
    assert finished.json()["summary"]["first_try_correct"] == len(_questions(view))
    assert _topic_row() is None and _stage_skill() is None and _observations() == []


def test_closed_reading_passage_can_record_reference_audio_before_finish(client):
    view = _topic(client, "assistance-reference-create").json()
    _read(client, view, "reference")
    first_question = _questions(view)[0]
    _post(client, view, first_question, "answer", "reference-first-answer", answer=_right(first_question))
    assert _support(client, view, view["items"][0]).status_code == 200
    for item in _questions(view)[1:]:
        _post(client, view, item, "answer", "reference-last-answer", answer=_right(item))
    completion = _finish(client, view, "reference-finish").json()["summary"]["completion"]
    assert completion["reason"] == "assisted" and not completion["counted"]
    again = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    questions = _questions(again)
    assert questions[0]["hint_used"] is False and questions[1]["hint_used"] is True
    assert _support(client, view, view["items"][0]).status_code == 409


def test_post_answer_reference_audio_does_not_rewrite_earlier_independent_answers(client):
    view = _topic(client, "post-answer-audio-create").json()
    _read(client, view, "post-answer-audio")
    _answer_questions(client, view, "post-answer-audio")
    assert _support(client, view, view["items"][0]).status_code == 200
    reloaded = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    assert reloaded["items"][0]["hint_used"] is True
    assert all(not item["hint_used"] for item in _questions(reloaded))
    result = _finish(client, view, "post-answer-audio-finish").json()["summary"]["completion"]
    assert result["counted"] and result["completed"]


def test_assisted_followup_never_erases_an_earlier_independent_completion(client):
    assert _run(client, "independent-before-audio", [True, True])["summary"]["completion"]["completed"]
    view = _topic(client, "assisted-after-complete").json()
    _support(client, view, view["items"][0])
    _read(client, view, "after-independent")
    _answer_questions(client, view, "after-independent")
    result = _finish(client, view, "after-independent-finish").json()["summary"]["completion"]
    assert not result["counted"] and result["reason"] == "assisted" and result["completed"]
    assert _topic_row()["completed"] is True and len(_observations()) == 1


def test_primary_listening_audio_is_not_a_hint_and_can_still_complete(client):
    view = _topic(client, "primary-listening-create", skill="listening").json()
    assert _support(client, view, view["items"][0]).status_code == 422
    _read(client, view, "primary-listening")
    _answer_questions(client, view, "primary-listening")
    completion = _finish(client, view, "primary-listening-finish").json()["summary"]["completion"]
    assert completion["counted"] and completion["completed"]


def test_legacy_answer_support_flag_also_persists_before_later_questions(client):
    view = _topic(client, "legacy-support-create").json()
    result = _post(client, view, view["items"][0], "answer", "legacy-support-passage",
                   answer={"done": True}, hint_used=True)
    assert result.status_code == 200
    resumed = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    assert all(item["hint_used"] for item in resumed["items"])
    _answer_questions(client, resumed, "legacy-support")
    completion = _finish(client, resumed, "legacy-support-finish").json()["summary"]["completion"]
    assert completion["reason"] == "assisted" and not completion["counted"]


def test_question_support_does_not_spread_to_unrelated_questions_but_does_prevent_independent_completion(client):
    view = _topic(client, "question-support-create").json()
    _read(client, view, "question-support")
    first, second = _questions(view)
    assert _support(client, view, first).status_code == 200
    resumed = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    values = {item["id"]: item["hint_used"] for item in resumed["items"]}
    assert values[first["id"]] and not values[second["id"]] and not values[view["items"][0]["id"]]
    _answer_questions(client, resumed, "question-support")
    assert _support(client, view, first).status_code == 409
    assert _finish(client, resumed, "question-support-finish").json()["summary"]["completion"]["reason"] == "assisted"


def test_support_endpoint_requires_owner_and_does_not_expose_other_learners_sessions(client):
    view = _topic(client, "support-owner-create").json()
    item = view["items"][0]
    assert _support(client, view, item, headers={}).status_code == 401
    assert _support(client, view, item, headers=auth_headers(email="second@example.com")).status_code == 404
    assert _support(client, view, {"id": str(uuid.uuid4())}).status_code == 404


@pytest.mark.parametrize("kind", ["listen_passage", "intro", "choice"])
def test_only_reading_passage_assistance_is_inherited(kind):
    passage = SimpleNamespace(kind=kind, hint_used=True, key={})
    question = SimpleNamespace(kind="choice", hint_used=False, key={"authored": True}, first_outcome=None, attempts=[])
    assert service._inherit_reading_assistance([passage, question]) is False
    assert question.hint_used is False
    passage.kind = "read_passage"
    assert service._inherit_reading_assistance([passage, question]) is True
    assert question.hint_used is True


def test_completion_uses_persisted_question_support_without_trusting_client_flags(monkeypatch):
    passage = SimpleNamespace(kind="read_passage", hint_used=True, key={})
    question = SimpleNamespace(kind="choice", hint_used=True, first_outcome="correct", attempts=[{}],
                               key={"authored": True})
    row = SimpleNamespace(skill="reading", topic_id="a1-t001", params={}, stage_id="a1", learner_id=uuid.uuid4())
    monkeypatch.setattr(service.activities, "stored_completion", lambda *args, **kwargs: True)
    result = service._completion(None, row, [passage, question])
    assert result["counted"] is False and result["reason"] == "assisted" and result["completed"] is True
    assert question.hint_used is True


def test_later_passage_support_preserves_first_answer_independence():
    passage = SimpleNamespace(kind="read_passage", hint_used=True, key={})
    earlier = SimpleNamespace(kind="choice", hint_used=False, key={"authored": True},
                              first_outcome="correct", attempts=[{}])
    later = SimpleNamespace(kind="choice", hint_used=False, key={"authored": True}, first_outcome=None, attempts=[])
    assert service._inherit_reading_assistance([passage, earlier, later]) is True
    assert earlier.hint_used is False and later.hint_used is True


def test_item_view_declares_support_but_still_drops_protected_fields():
    value = ItemView.model_validate({"id": uuid.uuid4(), "position": 0, "kind": "read_passage", "skill": "reading",
                                    "state": "open", "attempts_left": 1, "hint_used": True,
                                    "prompt": {"kind": "read_passage", "text": {"nl": "Een korte tekst."}},
                                    "key": {"answer": "secret"}}).model_dump()
    assert value["hint_used"] is True and "key" not in value
