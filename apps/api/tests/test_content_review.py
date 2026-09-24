"""Editorial suggestions stay administrator-only, source-bound, bounded and separate from approval."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from dlp.api.deps import settings_dep
from dlp.db.session import session_scope
from dlp.domains.content_review import service
from dlp.domains.content_review.models import ContentReview
from dlp.domains.content_review.schemas import ReviewReply, ReviewRequest
from dlp.domains.curriculum import topics
from dlp.domains.curriculum.models import CurriculumAttempt, TopicPractice
from dlp.domains.identity.models import Learner
from dlp.domains.jobs.models import Job
from dlp.domains.usage.models import UsageCounter
from dlp.providers.base import ProviderError
from dlp.providers.fixtures import FixtureChatModel
from dlp.providers.registry import get_providers


@pytest.fixture
def admin_settings(settings):
    return settings.model_copy(update={"curriculum_admin_emails": "owner@example.com", "usage_daily_tokens": 200000})


@pytest.fixture
def admin_client(client, admin_settings):
    from dlp.main import app
    app.dependency_overrides[settings_dep] = lambda: admin_settings
    yield client
    app.dependency_overrides.pop(settings_dep, None)


def review_reply(topic):
    return ReviewReply(summary="Een taalreviewer moet dit aandachtspunt beoordelen.", issues=[{
        "path": "reading.text.nl", "category": "difficulty", "quote": topic.reading.text.nl[:60],
        "explanation": "Controleer of deze tekst bij het beoogde niveau past.",
    }])


def providers_for(topic, *, failed=False, reply=None):
    providers = get_providers()
    provider = FixtureChatModel({service.POLICY_VERSION: reply or review_reply(topic).model_dump()}, fail_first=int(failed))
    provider.name = "test-editor"  # Test double, never a live-language verification.
    providers.chat_strong = provider
    return providers


def enqueue_one(client, headers):
    response = client.post("/content-review/a2", headers=headers, json={"topic_ids": ["a2-t001"]})
    assert response.status_code == 200, response.text
    with session_scope() as session:
        row = session.scalar(select(ContentReview))
        return row.id, session.get(Job, row.job_id).payload


def test_request_is_bounded_and_unique():
    for ids in ([], ["a2-t001"] * 2, [f"a2-t{i:03d}" for i in range(6)], ["x" * 61]):
        with pytest.raises(ValidationError):
            ReviewRequest(topic_ids=ids)
    assert len(ReviewRequest(topic_ids=["a2-t001"]).topic_ids) == 1


def test_schema_cannot_claim_approval_or_invent_categories():
    with pytest.raises(ValidationError):
        ReviewReply(summary="Goed", issues=[], approved=True)
    with pytest.raises(ValidationError):
        ReviewReply(summary="Goed", issues=[{"path": "title.nl", "category": "approved", "quote": "x", "explanation": "x"}])


@pytest.mark.parametrize("case", ["path", "quote", "duplicate"])
def test_output_must_cite_exact_supplied_content(case):
    topic = topics.topics_for("a2").topics[0]
    reply = review_reply(topic)
    if case == "path":
        reply.issues[0].path = "../../content/practice/a2.json"
    elif case == "quote":
        reply.issues[0].quote = "Dit citaat bestaat nergens in de tekst."
    else:
        reply.issues.append(reply.issues[0])
    with pytest.raises(ProviderError):
        service.validate_reply(topic, reply)


def test_cache_changes_with_source_policy_and_model(monkeypatch):
    topic = topics.topics_for("a2").topics[0]
    providers = providers_for(topic)
    first = service.versions("a2", topic, providers.chat_strong)[2]
    changed = topic.model_copy(deep=True)
    changed.reading.text.nl += " Extra tekst."
    assert first != service.versions("a2", changed, providers.chat_strong)[2]
    providers.chat_strong.model = "different-model"
    assert first != service.versions("a2", topic, providers.chat_strong)[2]
    providers.chat_strong.model = "fixture-chat-v1"
    monkeypatch.setattr(service, "POLICY_VERSION", "topic-editorial-v2")
    assert first != service.versions("a2", topic, providers.chat_strong)[2]


def test_allowlisted_learner_is_not_implicitly_an_editor(client, headers):
    assert client.get("/content-review/a2", headers=headers).status_code == 403
    assert client.post("/content-review/a2", headers=headers, json={"topic_ids": ["a2-t001"]}).status_code == 403
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(ContentReview)) == 0


def test_queue_is_cached_idempotent_and_no_learner_evidence_is_sent(admin_client, headers, admin_settings):
    topic = topics.topics_for("a2").topics[0]
    providers = providers_for(topic)
    row_id, payload = enqueue_one(admin_client, headers)
    again = admin_client.post("/content-review/a2", headers=headers, json={"topic_ids": ["a2-t001"]})
    assert again.status_code == 200
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(ContentReview)) == 1
        jobs = list(session.scalars(select(Job)))
        assert len(jobs) == 1 and jobs[0].max_attempts == 1
        assert service.process_review(session, payload, admin_settings, providers) == {"status": "needs_review"}
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "needs_review"
        row = session.get(ContentReview, row_id)
        assert row.result["issues"][0]["quote"] in topic.reading.text.nl
        assert row.status != "approved"
        assert session.scalar(select(func.count()).select_from(CurriculumAttempt)) == 0
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
    assert len(providers.chat_strong.calls) == 1
    supplied = " ".join(providers.chat_strong.calls[0]["messages"])
    assert "owner@example.com" not in supplied and "learner_response" not in supplied
    assert topics.topics_for("a2").review_status == "unreviewed"
    result = admin_client.get("/content-review/a2", headers=headers).json()["items"][0]["review"]
    assert result["status"] == "needs_review" and result["review_status"] == "unreviewed"
    assert "model_key" not in result and "requester_id" not in result


def test_failure_is_sanitized_conservatively_charged_and_explicitly_retried(admin_client, headers, admin_settings):
    topic = topics.topics_for("a2").topics[0]
    providers = providers_for(topic, failed=True)
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        result = service.process_review(session, payload, admin_settings, providers)
        assert result["status"] == "failed"
    with session_scope() as session:
        row = session.get(ContentReview, row_id)
        assert row.error_code == "review_unavailable" and row.result == {}
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "failed"
        calls = session.scalar(select(UsageCounter).where(UsageCounter.metric == "model_calls", UsageCounter.scope == "daily"))
        assert float(calls.used) == 1
    assert len(providers.chat_strong.calls) == 1
    response = admin_client.post("/content-review/a2", headers=headers,
                                 json={"topic_ids": ["a2-t001"], "retry_failed": True})
    assert response.status_code == 200
    with session_scope() as session:
        row = session.get(ContentReview, row_id)
        assert row.generation == 2
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "obsolete"
        current = session.get(Job, row.job_id)
        assert service.process_review(session, current.payload, admin_settings, providers)["status"] == "needs_review"
    assert len(providers.chat_strong.calls) == 2


def test_unusable_model_result_is_not_published(admin_client, headers, admin_settings):
    topic = topics.topics_for("a2").topics[0]
    reply = review_reply(topic).model_dump()
    reply["issues"][0]["path"] = "not_a_content_path"
    providers = providers_for(topic, reply=reply)
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "failed"
        assert session.get(ContentReview, row_id).result == {}
    assert len(providers.chat_strong.calls) == 1


def test_allowance_failure_makes_no_provider_call(admin_client, headers, admin_settings):
    providers = providers_for(topics.topics_for("a2").topics[0])
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        limited = admin_settings.model_copy(update={"usage_daily_tokens": 1})
        assert service.process_review(session, payload, limited, providers)["status"] == "failed"
        assert session.get(ContentReview, row_id).error_code == "allowance"
        calls = session.scalar(select(UsageCounter).where(UsageCounter.metric == "model_calls", UsageCounter.scope == "daily"))
        assert float(calls.used) == float(calls.reserved) == 0
    assert not providers.chat_strong.calls


def test_changed_content_invalidates_queued_and_cached_results(admin_client, headers, admin_settings, monkeypatch):
    providers = providers_for(topics.topics_for("a2").topics[0])
    row_id, payload = enqueue_one(admin_client, headers)
    changed = topics.topics_for("a2").model_copy(deep=True)
    changed.topics[0].reading.text.nl += " Nieuwe bronzin."
    monkeypatch.setattr(topics, "topics_for", lambda _: changed)
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "stale"
        assert session.get(ContentReview, row_id).result == {}
    assert not providers.chat_strong.calls
    page = admin_client.get("/content-review/a2", headers=headers).json()
    assert page["items"][0]["review"]["status"] == "stale"


def test_revoked_admin_and_interrupted_worker_never_call_model(admin_client, headers, admin_settings):
    providers = providers_for(topics.topics_for("a2").topics[0])
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        revoked = admin_settings.model_copy(update={"curriculum_admin_emails": ""})
        assert service.process_review(session, payload, revoked, providers)["status"] == "failed"
        assert session.get(ContentReview, row_id).error_code == "access_changed"
        session.get(ContentReview, row_id).status = "running"
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "failed"
        assert session.get(ContentReview, row_id).error_code == "interrupted"
    assert not providers.chat_strong.calls


def test_concurrent_requests_create_one_job(admin_client, headers, admin_settings):
    admin_client.get("/curriculum", headers=headers)
    providers = providers_for(topics.topics_for("a2").topics[0])
    with session_scope() as session:
        learner_id = session.scalar(select(Learner.id))
    def queue(_):
        with session_scope() as session:
            return service.queue_topics(session, admin_settings, providers, requester_id=learner_id,
                                        stage_id="a2", topic_ids=["a2-t001"], retry_failed=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(queue, [1, 2]))
    assert len(results) == 2
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(ContentReview)) == 1
        assert session.scalar(select(func.count()).select_from(Job)) == 1


def test_deleted_requester_cannot_leave_replayable_private_job(admin_client, headers, admin_settings):
    providers = providers_for(topics.topics_for("a2").topics[0])
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        row = session.get(ContentReview, row_id)
        session.delete(session.get(Learner, row.requester_id))
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "obsolete"
    assert not providers.chat_strong.calls


def test_development_fixture_never_looks_like_editorial_review(admin_client, headers, admin_settings):
    providers = get_providers()
    providers.chat_strong = FixtureChatModel()
    row_id, payload = enqueue_one(admin_client, headers)
    with session_scope() as session:
        assert service.process_review(session, payload, admin_settings, providers)["status"] == "development_only"
        row = session.get(ContentReview, row_id)
        assert row.result["issues"] == []
        assert "geen taalcontrole" in row.result["summary"]
    assert not providers.chat_strong.calls


def test_azure_without_paid_approval_never_calls_model(admin_client, headers, admin_settings):
    providers = providers_for(topics.topics_for("a2").topics[0])
    row_id, payload = enqueue_one(admin_client, headers)
    denied = admin_settings.model_copy(update={"chat_provider": "azure", "paid_usage_enabled": False})
    with session_scope() as session:
        assert service.process_review(session, payload, denied, providers)["status"] == "failed"
        assert session.get(ContentReview, row_id).error_code == "paid_not_approved"
    assert not providers.chat_strong.calls


def test_expired_job_lease_cannot_cause_concurrent_provider_calls(admin_client, headers, admin_settings):
    providers = providers_for(topics.topics_for("a2").topics[0])
    _, payload = enqueue_one(admin_client, headers)
    entered, release = Event(), Event()
    original = providers.chat_strong.complete_once
    def waiting(*args, **kwargs):
        entered.set()
        assert release.wait(10), "test did not release the provider"
        return original(*args, **kwargs)
    providers.chat_strong.complete_once = waiting
    def process():
        with session_scope() as session:
            return service.process_review(session, payload, admin_settings, providers)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(process)
        assert entered.wait(10), "first worker did not reach the provider"
        second = pool.submit(process)
        release.set()
        assert first.result(timeout=10)["status"] == "needs_review"
        assert second.result(timeout=10)["status"] == "needs_review"
    assert len(providers.chat_strong.calls) == 1
