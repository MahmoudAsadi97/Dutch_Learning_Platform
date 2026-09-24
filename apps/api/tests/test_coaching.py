"""Grounded practice selection, append-only evidence, idempotency and bounded optional ordering."""
from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from dlp.db.base import utcnow
from dlp.db.session import session_scope
from dlp.domains.coaching import service
from dlp.domains.coaching.models import CoachPlanRequest, PracticeObservation
from dlp.domains.coaching.schemas import PlanRanking
from dlp.domains.curriculum import topics
from dlp.domains.curriculum.models import CurriculumAttempt, CurriculumPractice, TopicPractice
from dlp.domains.curriculum.service import word_count
from dlp.domains.identity.models import Learner
from dlp.domains.usage.models import UsageCounter
from dlp.providers.base import ChatResult, ProviderError
from dlp.providers.registry import get_providers

from .conftest import auth_headers
from .test_curriculum import answers, install_assessor


@pytest.fixture
def bank():
    return topics.topics_for("a2")


def episode(bank, *, topic_index=0, skill="reading", passed=False, created=None, source="topic_practice"):
    version = hashlib.sha256(bank.topics[topic_index].model_dump_json().encode()).hexdigest()
    return PracticeObservation(id=uuid.uuid4(), learner_id=uuid.uuid4(), stage_id=bank.stage_id,
                               topic_id=bank.topics[topic_index].id, skill=skill, source=source,
                               request_id=uuid.uuid4().hex, content_version=version, payload_hash="b" * 64,
                               passed=passed, summary={"assessed": passed is not None, "topic_content_version": version},
                               failed_refs=[],
                               response={}, created_at=created or utcnow())


def test_fresh_plan_has_three_real_localized_activities_without_claiming_weakness(bank):
    plan, evidence = service.candidate_plan(bank, [], 0)
    assert plan["mode"] == "suggested" and not plan["can_personalise"]
    assert len(plan["items"]) == len({item["id"] for item in plan["items"]}) == 3
    assert all(item["basis"] == "start" and item["evidence_count"] == 0 for item in plan["items"])
    assert all(item["topic_id"] in {topic.id for topic in bank.topics} for item in plan["items"])
    assert set(item["skill"] for item in plan["items"]) == {"reading", "listening", "speaking"}
    assert all(all(item["reason"][lang] for lang in ("nl", "en", "fa")) for item in plan["items"])
    assert not any(evidence.values())


def test_a_single_attempt_cannot_be_called_a_recurring_problem(bank):
    first = episode(bank)
    plan, evidence = service.candidate_plan(bank, [first], 1)
    assert plan["items"][0]["basis"] == "recent_attempt"
    assert plan["items"][0]["evidence_count"] == 1
    assert evidence[plan["items"][0]["id"]] == [str(first.id)]
    assert plan["items"][1]["basis"] == "transfer"
    assert plan["items"][1]["topic_id"] != first.topic_id
    assert plan["items"][2]["basis"] == "unpractised_skill"
    assert plan["items"][2]["skill"] != first.skill


def test_two_distinct_observed_attempts_are_needed_for_repeated_label(bank):
    first, second = episode(bank), episode(bank)
    duplicate_plan, _ = service.candidate_plan(bank, [first, first], 1)
    assert duplicate_plan["items"][0]["basis"] == "recent_attempt"
    plan, _ = service.candidate_plan(bank, [first, second], 2)
    assert plan["items"][0]["basis"] == "repeated_attempts"
    assert plan["items"][0]["evidence_count"] == 2
    assert "grammar" not in json.dumps(plan)


def test_successful_retry_retires_the_previous_failure_suggestion(bank):
    failed, passed = episode(bank), episode(bank, passed=True)
    plan, _ = service.candidate_plan(bank, [passed, failed], 2)
    assert plan["items"][0]["basis"] == "transfer"
    assert not any(item["basis"] in ("recent_attempt", "repeated_attempts") for item in plan["items"])
    assert "master" not in json.dumps(plan).lower()


def test_unassessed_and_typed_work_never_become_a_speaking_weakness(bank):
    unknown = episode(bank, passed=None, skill="speaking")
    typed = episode(bank, skill="writing", source="conversation")
    plan, _ = service.candidate_plan(bank, [typed, unknown], 2)
    assert plan["items"][0]["skill"] == "writing" and plan["items"][0]["basis"] == "recent_attempt"
    assert not any(item["skill"] == "speaking" and item["basis"] in ("recent_attempt", "repeated_attempts")
                   for item in plan["items"])


def test_observations_from_an_old_content_version_cannot_diagnose_a_current_weakness(bank):
    old = episode(bank)
    old.content_version = "outdated"
    plan, _ = service.candidate_plan(bank, [old], 1)
    assert plan["items"][0]["basis"] == "transfer"
    assert not any(item["basis"] in ("recent_attempt", "repeated_attempts") for item in plan["items"])


@pytest.mark.parametrize("case", ["invented", "duplicate", "foreign-evidence", "omitted-evidence", "duplicate-evidence"])
def test_model_cannot_invent_activity_or_observation_ids(bank, case):
    plan, refs = service.candidate_plan(bank, [episode(bank)], 1)
    rows = [{"id": item["id"], "evidence_ids": refs[item["id"]]} for item in plan["items"]]
    if case == "invented":
        rows[0]["id"] = "c2-t099:writing"
    elif case == "duplicate":
        rows[1] = deepcopy(rows[0])
    elif case == "foreign-evidence":
        rows[0]["evidence_ids"] = [str(uuid.uuid4())]
    elif case == "omitted-evidence":
        rows[0]["evidence_ids"] = []
    else:
        rows[0]["evidence_ids"] *= 2
    with pytest.raises(ProviderError):
        service.validate_ranking(PlanRanking.model_validate({"activities": rows}), plan, refs)


def test_model_only_reorders_code_authored_reasons(bank):
    plan, refs = service.candidate_plan(bank, [episode(bank)], 1)
    rows = [{"id": item["id"], "evidence_ids": refs[item["id"]]} for item in reversed(plan["items"])]
    ordered = service.validate_ranking(PlanRanking.model_validate({"activities": rows}), plan, refs)
    assert ordered == list(reversed(plan["items"]))


def owner_id(client, headers):
    assert client.get("/curriculum", headers=headers).status_code == 200
    with session_scope() as db:
        return db.scalar(select(Learner.id).where(Learner.email == "owner@example.com"))


def bounded_writing(topic):
    """A test transcript that meets bounds; excerpts are not complete learner submissions."""
    sample = topic.writing.sample.nl
    while word_count(sample) < topic.writing.min_words:
        sample += " " + topic.writing.sample.nl
    return " ".join(sample.split()[:topic.writing.max_words])


def record(db, owner, bank, *, request_id=None, payload=None, skill="reading", passed=False, topic_index=0):
    return service.record_observation(
        db, learner_id=owner, stage_id=bank.stage_id, topic_id=bank.topics[topic_index].id, skill=skill,
        source="topic_practice", request_id=request_id or uuid.uuid4().hex,
        content_version=hashlib.sha256(bank.topics[topic_index].model_dump_json().encode()).hexdigest(),
        passed=passed, summary={"assessed": passed is not None}, failed_refs=["question-1"] if not passed else [],
        payload=payload or {"answer": 1}, response={"passed": passed},
    )


def test_get_plan_and_history_are_scoped_bounded_read_only_and_do_not_call_models(client, headers, bank, monkeypatch):
    assert client.get("/coach/plan?stage_id=a2").status_code == 401
    def forbidden(*args, **kwargs):
        pytest.fail("GET must not call a model")
    monkeypatch.setattr(get_providers().chat, "complete_once", forbidden)
    owner = owner_id(client, headers)
    with session_scope() as db:
        record(db, owner, bank)
    mine = client.get("/coach/plan?stage_id=a2", headers=headers).json()
    assert mine["history_count"] == 1 and mine["items"][0]["basis"] == "recent_attempt"
    other = client.get("/coach/plan?stage_id=a2", headers=auth_headers(email="second@example.com")).json()
    assert other["history_count"] == 0 and not other["can_personalise"]
    other_history = client.get("/coach/history?stage_id=a2", headers=auth_headers(email="second@example.com"))
    assert other_history.json()["items"] == []
    assert len(client.get("/coach/history?stage_id=a2&limit=1", headers=headers).json()["items"]) == 1
    assert client.get("/coach/history?stage_id=a2&limit=51", headers=headers).status_code == 422
    assert client.get("/coach/plan?stage_id=a3", headers=headers).status_code == 404
    with session_scope() as db:
        for model in (CoachPlanRequest, TopicPractice, CurriculumPractice, CurriculumAttempt, UsageCounter):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_observations_are_append_only_deduplicate_retries_and_reject_conflicting_payload(client, headers, bank):
    owner = owner_id(client, headers)
    key = uuid.uuid4().hex
    with session_scope() as db:
        first = record(db, owner, bank, request_id=key)
        repeat = record(db, owner, bank, request_id=key)
        assert first.id == repeat.id
        assert len(service.export_observations(db, owner)) == 1
    with session_scope() as db:
        with pytest.raises(service.CurriculumError) as error:
            record(db, owner, bank, request_id=key, payload={"answer": 2})
        assert error.value.status_code == 409
    with session_scope() as db:
        record(db, owner, bank, passed=True)
        history = service.export_observations(db, owner)
        assert len(history) == 2 and history[0]["passed"] is False and history[1]["passed"] is True
        assert "payload_hash" not in history[0] and "response" not in history[0]


def test_topic_submission_history_replay_does_not_pay_or_mutate_progress_twice(client, headers, bank, monkeypatch):
    topic = bank.topics[0]
    key = uuid.uuid4().hex
    calls = install_assessor(monkeypatch)
    body = {"request_id": key, "skill": "writing", "text": bounded_writing(topic)}
    path = f"/curriculum/a2/topics/{topic.id}/practice"
    first = client.post(path, headers=headers, json=body)
    assert first.status_code == 200, first.text
    second = client.post(path, headers=headers, json=body)
    assert second.status_code == 200 and second.json() == first.json()
    assert len(calls) == 1
    changed = client.post(path, headers=headers, json={**body, "text": body["text"] + " Dag."})
    assert changed.status_code == 409 and len(calls) == 1
    with session_scope() as db:
        assert db.scalar(select(func.count()).select_from(PracticeObservation)) == 1
        assert db.scalar(select(func.count()).select_from(TopicPractice)) == 1


def test_receptive_history_records_each_deliberate_attempt_and_fixture_feedback_is_unassessed(client, headers, bank):
    topic = bank.topics[0]
    path = f"/curriculum/a2/topics/{topic.id}/practice"
    correct = answers(topic.reading.questions)
    wrong = {q.id: (q.answer_index + 1) % len(q.options) for q in topic.reading.questions}
    for answer_set in (wrong, correct):
        result = client.post(path, headers=headers, json={"skill": "reading", "answers": answer_set})
        assert result.status_code == 200, result.text
    result = client.post(path, headers=headers, json={"skill": "writing", "text": bounded_writing(topic)})
    assert result.status_code == 200, result.text
    with session_scope() as db:
        rows = list(db.scalars(select(PracticeObservation).order_by(PracticeObservation.created_at)))
        assert len(rows) == 3 and [row.passed for row in rows] == [False, True, None]
        assert rows[0].failed_refs and not rows[1].failed_refs and not rows[2].failed_refs
        assert rows[0].summary["correct"] == 0


def install_ranker(monkeypatch, *, failure=False, hallucination=False):
    provider = get_providers().chat
    monkeypatch.setattr(provider, "name", "test-small")
    calls = []
    def complete_once(messages, **kwargs):
        candidates = json.loads(messages[-1].content)["candidates"]
        calls.append((messages, kwargs))
        if failure:
            raise ProviderError("uncertain transport failure")
        rows = [{"id": item["id"], "evidence_ids": item["evidence_ids"]} for item in reversed(candidates)]
        if hallucination:
            rows[0]["id"] = "imaginary-lesson"
        reply = PlanRanking.model_validate({"activities": rows})
        return ChatResult(text=reply.model_dump_json(), parsed=reply, provider="test-small", model="test",
                          prompt_version=service.POLICY_VERSION, input_tokens=20, output_tokens=40,
                          latency_ms=1, attempts=1)
    monkeypatch.setattr(provider, "complete_once", complete_once)
    return calls


def test_optional_ordering_is_cached_by_history_not_every_request_or_page_view(client, headers, bank, monkeypatch):
    owner = owner_id(client, headers)
    with session_scope() as db:
        record(db, owner, bank)
    calls = install_ranker(monkeypatch)
    key = uuid.uuid4().hex
    first = client.post("/coach/plan", headers=headers, json={"stage_id": "a2", "request_id": key})
    assert first.status_code == 200 and first.json()["mode"] == "personalised", first.text
    assert not first.json()["can_personalise"]
    for body in ({"stage_id": "a2", "request_id": key}, {"stage_id": "a2", "request_id": uuid.uuid4().hex}):
        assert client.post("/coach/plan", headers=headers, json=body).json() == first.json()
    assert client.get("/coach/plan?stage_id=a2", headers=headers).json() == first.json()
    assert len(calls) == 1
    assert client.post("/coach/plan", headers=headers, json={"stage_id": "b1", "request_id": key}).status_code == 409
    with session_scope() as db:
        record(db, owner, bank, skill="writing")
    updated = client.post("/coach/plan", headers=headers, json={"stage_id": "a2", "request_id": uuid.uuid4().hex})
    assert updated.json()["history_version"] != first.json()["history_version"]
    assert len(calls) == 2
    assert all(call[1]["max_output_tokens"] == 600 for call in calls)
    assert all("learner_response" not in call[0][-1].content for call in calls)


@pytest.mark.parametrize("case", ["outage", "hallucination", "limit"])
def test_ordering_fallback_remains_useful_and_charges_uncertain_work(client, headers, bank, monkeypatch, settings, case):
    owner = owner_id(client, headers)
    with session_scope() as db:
        record(db, owner, bank)
    calls = install_ranker(monkeypatch, failure=case == "outage", hallucination=case == "hallucination")
    if case == "limit":
        monkeypatch.setattr(settings, "usage_daily_model_calls", 0)
    result = client.post("/coach/plan", headers=headers, json={"stage_id": "a2", "request_id": uuid.uuid4().hex})
    assert result.status_code == 200 and result.json()["mode"] == "fallback", result.text
    assert not result.json()["can_personalise"]
    assert len(result.json()["items"]) == 3
    assert len(calls) == (0 if case == "limit" else 1)
    with session_scope() as db:
        counters = list(db.scalars(select(UsageCounter).where(UsageCounter.scope == "daily")))
        if case != "limit":
            assert next(row for row in counters if row.metric == "model_calls").used == 1
            tokens = next(row for row in counters if row.metric == "tokens")
            assert tokens.used > 60 if case == "outage" else tokens.used == 60
        assert all(row.reserved == 0 for row in counters)


def test_empty_history_ordering_stays_free_and_does_not_award_progress(client, headers, monkeypatch):
    calls = install_ranker(monkeypatch)
    result = client.post("/coach/plan", headers=headers, json={"stage_id": "c2", "request_id": uuid.uuid4().hex})
    assert result.status_code == 200 and result.json()["mode"] == "suggested" and not calls
    progress = client.get("/curriculum/c2", headers=headers).json()["progress"]
    assert not progress["passed"] and not progress["practice_completed"]


def test_other_paid_role_in_flight_refuses_coach_before_provider_or_reservation(client, headers, bank, monkeypatch):
    owner = owner_id(client, headers)
    with session_scope() as db:
        record(db, owner, bank)
    calls = install_ranker(monkeypatch)
    with session_scope() as busy:
        service.paid_model_guard(busy, owner)
        response = client.post("/coach/plan", headers=headers,
                               json={"stage_id": "a2", "request_id": uuid.uuid4().hex})
        assert response.status_code == 409 and not calls
        with session_scope() as independent:
            service.paid_model_guard(independent, uuid.uuid4())
    with session_scope() as db:
        assert db.scalar(select(func.count()).select_from(UsageCounter)) == 0
        service.paid_model_guard(db, owner)  # The guard is released with the previous transaction.


def test_history_window_is_bounded_and_export_and_deletion_stay_learner_owned(client, headers, bank):
    owner = owner_id(client, headers)
    with session_scope() as db:
        for index in range(105):
            row = record(db, owner, bank)
            row.created_at = utcnow() - timedelta(minutes=index)
        db.flush()
        rows, count = service._history(db, owner, bank.stage_id)
        assert len(rows) == 100 and count == 105
        assert len(service.export_observations(db, owner)) == 105
    assert len(client.get("/coach/history?stage_id=a2&limit=50&offset=100", headers=headers).json()["items"]) == 5
    assert client.post("/coach/plan", headers=headers,
                       json={"stage_id": "a2", "request_id": uuid.uuid4().hex}).status_code == 200
    with session_scope() as db:
        db.delete(db.get(Learner, owner))
    with session_scope() as db:
        assert db.scalar(select(func.count()).select_from(PracticeObservation)) == 0
        assert db.scalar(select(func.count()).select_from(CoachPlanRequest)) == 0
