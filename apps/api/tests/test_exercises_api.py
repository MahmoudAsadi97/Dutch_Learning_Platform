"""Exercise sessions over HTTP: create, resume, answer, skip, finish; keys, points, mistakes and the export."""
from __future__ import annotations

import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

from dlp.db.session import session_scope
from dlp.domains.activity.day import local_today
from dlp.domains.activity.models import ActivityEvent, LearningDay
from dlp.domains.activity.service import add_to_day
from dlp.domains.exercises import pool, service
from dlp.domains.exercises.models import ExerciseItem, ExerciseSession, LearnerMistake, WordSuggestion
from dlp.domains.exercises.pool import pool_for
from dlp.domains.exercises.schemas import AnswerValue
from dlp.domains.identity.models import Learner
from tests.conftest import auth_headers

SECRETS = {"answer", "support", "explanation", "met", "words", "key"}


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def _create(client, request_id="exercise-session-0001", *, email="owner@example.com", **body):
    return client.post("/exercises/sessions", headers=auth_headers(email=email),
                       json={"request_id": request_id, "stage_id": "a1", **body})


def _post(client, view, item, action="answer", *, request_id, email="owner@example.com", **body):
    return client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}",
                       headers=auth_headers(email=email), json={"request_id": request_id, **body})


def _key(item) -> dict:
    with session_scope() as session:
        return session.scalar(select(ExerciseItem.key).where(ExerciseItem.id == uuid.UUID(item["id"])))


def _right(item) -> dict:
    return {"option": _key(item)["answer"]}


def _wrong(item) -> dict:
    answer = _key(item)["answer"]
    return {"option": next(option["id"] for option in item["prompt"]["options"] if option["id"] != answer)}


def _graded(view) -> list[dict]:
    return [item for item in view["items"] if item["kind"] != "intro"]


def _learner_id(email="owner@example.com"):
    with session_scope() as session:
        return session.scalar(select(Learner.id).where(Learner.email == email))


def _day():
    with session_scope() as session:
        return session.scalar(select(LearningDay).where(LearningDay.learner_id == _learner_id(),
                                                        LearningDay.day == local_today()))


def test_a_session_opens_with_the_new_words_and_shows_no_answer(client):
    created = _create(client)
    assert created.status_code == 200, created.text
    view = created.json()
    assert view["status"] == "active" and view["content_status"] == "unreviewed" and not view["resumed"]
    intro, graded = view["items"][0], _graded(view)
    assert intro["kind"] == "intro" and view["next_item_id"] == intro["id"]
    assert len(graded) == 8 and view["progress"] == {"closed": 0, "total": 8, "queued": 0}
    assert not _keys(graded) & SECRETS, "no key, gloss of a Dutch option or met-list before answering"
    assert {item["kind"] for item in graded} <= {"choice", "cloze_choice", "odd_one_out"}
    assert all(item["attempts_left"] == 2 and item["feedback"] is None for item in graded)


def test_the_same_request_is_the_same_session_and_another_resumes_it(client):
    first = _create(client).json()
    assert _create(client).json() == first, "a repeated create returns the stored session"
    resumed = _create(client, "exercise-session-0002").json()
    assert resumed["id"] == first["id"] and resumed["resumed"]
    fresh = _create(client, "exercise-session-0003", fresh=True).json()
    assert fresh["id"] != first["id"]
    old = client.get(f"/exercises/sessions/{first['id']}", headers=auth_headers()).json()
    assert old["status"] == "abandoned" and old["next_item_id"] is None
    reused = _create(client, size=6)
    assert reused.status_code == 409 and reused.json()["code"] == "exercise"


def test_an_answer_closes_its_item_once_and_a_retry_replays_it(client):
    view = _create(client).json()
    intro, item = view["items"][0], _graded(view)[0]
    done = _post(client, view, intro, request_id="answer-intro-01", answer={"done": True}).json()
    assert done["outcome"] == "done" and done["closed"] and done["points"] == 0
    answer = _post(client, view, item, request_id="answer-item-001", answer=_right(item))
    body = answer.json()
    assert answer.status_code == 200, answer.text
    assert (body["outcome"], body["closed"], body["requeue"], body["points"]) == ("correct", True, False, 1)
    feedback = body["feedback"]
    assert feedback["correct"] == feedback["given"] == _key(item)["answer"] and len(feedback["support"]) == 4
    assert feedback["word"]["term"] and body["progress"] == {"closed": 1, "total": 8, "queued": 0}
    again = _post(client, view, item, request_id="answer-item-001", answer=_right(item)).json()
    assert again == body, "the stored response"
    other = _post(client, view, item, request_id="answer-item-001", answer=_wrong(item))
    assert other.status_code == 409 and other.json()["code"] == "exercise"
    closed = _post(client, view, item, request_id="answer-item-002", answer=_right(item))
    assert closed.status_code == 409 and closed.json()["code"] == "already_answered"
    assert _post(client, view, item, request_id="answer-item-003", answer={"option": "zzzz"}).status_code == 409
    day = _day()
    assert day.exercise_items == 1 and day.points == 1


def test_a_miss_shows_the_answer_and_comes_back_once_at_the_end(client):
    view = _create(client).json()
    item = _graded(view)[0]
    miss = _post(client, view, item, request_id="answer-miss-001", answer=_wrong(item)).json()
    assert (miss["outcome"], miss["closed"], miss["requeue"], miss["attempts_left"]) == ("incorrect", False, True, 1)
    assert miss["feedback"]["correct"] == _key(item)["answer"] and miss["points"] == 0
    assert miss["progress"]["queued"] == 1 and miss["next_item_id"] != item["id"]
    reread = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    again = next(entry for entry in reread["items"] if entry["id"] == item["id"])
    assert again["state"] == "open" and again["attempts_left"] == 1 and again["feedback"] is None
    assert {o["id"] for o in again["prompt"]["options"]} == {o["id"] for o in item["prompt"]["options"]}
    second = _post(client, view, again, request_id="answer-miss-002", answer=_wrong(item)).json()
    assert (second["outcome"], second["closed"], second["points"]) == ("incorrect", True, 1), "effort counts"
    unknown = _post(client, view, item, request_id="answer-miss-003", answer={"option": "zzzz"})
    assert unknown.status_code == 409


def test_a_skip_comes_back_once_and_two_skips_earn_nothing(client):
    view = _create(client).json()
    item = _graded(view)[1]
    first = _post(client, view, item, "skip", request_id="skip-item-0001").json()
    assert (first["outcome"], first["requeue"], first["feedback"]["correct"]) == ("skipped", True, _key(item)["answer"])
    second = _post(client, view, item, "skip", request_id="skip-item-0002").json()
    assert (second["outcome"], second["closed"], second["points"]) == ("skipped", True, 0)


def test_an_option_outside_the_item_is_refused(client):
    view = _create(client).json()
    item = _graded(view)[0]
    refused = _post(client, view, item, request_id="answer-bad-0001", answer={"option": "zzzz"})
    assert refused.status_code == 422 and refused.json()["code"] == "exercise"
    intro = view["items"][0]
    assert _post(client, view, intro, request_id="answer-bad-0002", answer={"option": "zzzz"}).status_code == 422


def test_a_first_encounter_is_no_mistake_and_a_word_met_before_is(client):
    view = _create(client).json()
    first = _graded(view)[0]
    _post(client, view, first, request_id="mistake-new-0001", answer=_wrong(first))
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(LearnerMistake)) == 0
    client.post("/words", headers=auth_headers(), json={"term": "de ochtend", "meaning_en": "morning"})
    ochtend = next(word for word in pool_for("a1").words if word.term == "de ochtend")
    later = _create(client, "mistake-met-00001", fresh=True).json()
    item = next(item for item in _graded(later) if item["id"] and _key(item).get("word", {}).get("library_id")
                == ochtend.id and _key(item)["word"]["term"] == "de ochtend")
    _post(client, later, item, request_id="mistake-met-00002", answer=_wrong(item))
    with session_scope() as session:
        mistake = session.scalar(select(LearnerMistake))
        assert mistake is not None and mistake.lemma == "ochtend" and mistake.source == "exercise"
        assert mistake.category in ("vocabulary_meaning", "word_choice") and mistake.expected == "de ochtend"
        assert mistake.taxonomy_version == "t1" and mistake.assessed and mistake.source_id == item["id"]


def test_finishing_needs_every_item_unless_early_and_says_the_same_twice(client):
    view = _create(client).json()
    refused = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                          json={"request_id": "finish-early-001"})
    assert refused.status_code == 409 and refused.json()["code"] == "exercise"
    item = _graded(view)[0]
    _post(client, view, item, request_id="finish-early-002", answer=_wrong(item))
    early = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                        json={"request_id": "finish-early-003", "early": True}).json()
    assert early["status"] == "finished" and early["points"] == 0, "no bonus under five items"
    summary = early["summary"]
    assert (summary["items_total"], summary["answered"], summary["skipped"], summary["session_bonus"]) == (8, 0, 0, 0)
    assert summary["missed"][0]["term"] and [s["term"] for s in summary["suggestions"]] == [summary["missed"][0]["term"]]
    again = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                        json={"request_id": "finish-early-004"}).json()
    assert again["summary"] == summary and again["points"] == 0
    late = _post(client, view, _graded(view)[2], request_id="finish-early-005", answer=_right(_graded(view)[2]))
    assert late.status_code == 409 and late.json()["code"] == "session_closed"


def test_a_whole_session_earns_its_items_and_the_bonus(client):
    view = _create(client).json()
    _post(client, view, view["items"][0], request_id="whole-intro-001", answer={"done": True})
    for index, item in enumerate(_graded(view)):
        assert _post(client, view, item, request_id=f"whole-item-{index:04d}", answer=_right(item)).status_code == 200
    finished = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                           json={"request_id": "whole-finish-01"}).json()
    summary = finished["summary"]
    assert finished["points"] == 5 and summary["points_earned"] == 13 and summary["first_try_correct"] == 8
    assert summary["missed"] == [] and summary["suggestions"] == []
    assert sum(kind["total"] for kind in summary["by_kind"].values()) == 8
    day = _day()
    assert (day.points, day.exercise_items, day.exercise_sessions) == (13, 8, 1)


def test_the_goal_moment_reaches_the_answer_that_crosses_it(client):
    view = _create(client).json()
    with session_scope() as session:
        add_to_day(session, _learner_id(), day=local_today(), points=19)
    item = _graded(view)[0]
    crossed = _post(client, view, item, request_id="goal-cross-0001", answer=_right(item)).json()
    assert crossed["goal_reached"] is True
    replay = _post(client, view, item, request_id="goal-cross-0001", answer=_right(item)).json()
    assert replay["goal_reached"] is True, "a retried crossing says so again"


def test_another_learner_sees_nothing(client):
    view = _create(client).json()
    item = _graded(view)[0]
    other = auth_headers(email="second@example.com")
    assert client.get(f"/exercises/sessions/{view['id']}", headers=other).status_code == 404
    assert _post(client, view, item, request_id="other-learner-01", email="second@example.com",
                 answer=_right(item)).status_code == 404


def test_unknown_stage_or_topic_and_a_thin_stage(client, monkeypatch):
    assert _create(client, "unknown-stage-001", stage_id="z9").status_code == 404
    assert _create(client, "unknown-topic-001", library_topic="Nergens").status_code == 404
    topic = pool_for("a1").topics[2]
    focused = _create(client, "known-topic-0001", library_topic=topic).json()
    assert focused["library_topic"] == topic
    monkeypatch.setattr(pool, "VARIETY_MIN_CHOICE_WORDS", 10_000)
    thin = _create(client, "thin-stage-00001", stage_id="a2")
    assert thin.status_code == 409 and thin.json()["code"] == "not_ready"


def test_the_level_comes_from_the_profile_and_waiting_is_short(client):
    view = client.post("/exercises/sessions", headers=auth_headers(),
                       json={"request_id": "while-waiting-01", "source": "while_you_wait"}).json()
    assert view["stage_id"] == client.get("/me", headers=auth_headers()).json()["profile"]["stage_id"]
    assert len(_graded(view)) == 5


def test_two_tabs_answering_at_once_record_one_attempt(client):
    view = _create(client).json()
    item = _graded(view)[0]
    learner_id, option = _learner_id(), _right(item)["option"]
    barrier = Barrier(2)

    def answer(_):
        with session_scope() as session:
            barrier.wait(timeout=10)
            return service.respond(session, learner_id, uuid.UUID(view["id"]), uuid.UUID(item["id"]),
                                   request_id="two-tabs-000001", answer=AnswerValue(option=option))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(answer, [1, 2]))
    assert results[0]["attempt"] == results[1]["attempt"] == 1
    with session_scope() as session:
        stored = session.scalar(select(ExerciseItem).where(ExerciseItem.id == uuid.UUID(item["id"])))
        assert len(stored.attempts) == 1 and stored.points_awarded == 1
        assert session.scalar(select(func.count()).select_from(ActivityEvent)
                              .where(ActivityEvent.kind == "exercise_item")) == 1


def test_the_export_carries_practice_without_keys_and_deletion_removes_it(client):
    client.post("/words", headers=auth_headers(), json={"term": "de ochtend", "meaning_en": "morning"})
    view = _create(client).json()
    for index, item in enumerate(_graded(view)):
        _post(client, view, item, request_id=f"export-item-{index:04d}", answer=_wrong(item))
    client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                json={"request_id": "export-finish-01", "early": True})
    payload = client.get("/export", headers=auth_headers()).json()
    sessions = payload["exercises"]
    assert len(sessions) == 1 and len(sessions[0]["items"]) == 9 and "fingerprint" not in sessions[0]["params"]
    graded = [item for row in sessions for item in row["items"] if item["kind"] != "intro"]
    assert not _keys(graded) & SECRETS, "no item key in the export"
    assert payload["mistakes"] and all(m["source"] == "exercise" for m in payload["mistakes"])
    assert payload["word_suggestions"] and payload["word_suggestions"][0]["reason"] == "missed"
    with session_scope() as session:
        session.delete(session.get(Learner, _learner_id()))
    with session_scope() as session:
        for model in (ExerciseSession, ExerciseItem, LearnerMistake, WordSuggestion):
            assert session.scalar(select(func.count()).select_from(model)) == 0


def test_the_migration_is_additive_and_deletes_with_the_learner():
    root = Path(__file__).resolve().parents[1]
    output = io.StringIO()
    config = Config(str(root / "alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "0009:0010", sql=True)
    sql = output.getvalue()
    for table in ("exercise_sessions", "exercise_items", "learner_mistakes", "word_suggestions"):
        assert f"CREATE TABLE {table}" in sql
    assert sql.count("REFERENCES learners (id) ON DELETE CASCADE") == 4
    assert "REFERENCES exercise_sessions (id) ON DELETE CASCADE" in sql
    assert "DROP TABLE" not in sql
