import threading
import uuid

import pytest

from dlp.db.session import session_scope
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.service import get_or_create_learner
from dlp.domains.usage import service as usage
from dlp.domains.usage.service import UsageLimitExceeded


@pytest.fixture
def learner_id(database) -> uuid.UUID:
    with session_scope() as session:
        learner = get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com", "Owner",
                                                           "fixture", "req-0001"))
        return learner.id


def test_reserve_commit_release_cycle(settings, learner_id):
    with session_scope() as session:
        reservation = usage.reserve(session, settings, learner_id, "audio_seconds", 10, "req-a")
        assert not reservation.deduplicated
        snap = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
        assert snap["daily"]["reserved"] == 10 and snap["daily"]["used"] == 0
        usage.commit(session, reservation.id, 7.5)
        snap = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
        assert snap["daily"]["reserved"] == 0 and snap["daily"]["used"] == 7.5
        assert snap["total"]["used"] == 7.5

        second = usage.reserve(session, settings, learner_id, "audio_seconds", 5, "req-b")
        usage.release(session, second.id)
        snap = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
        assert snap["daily"]["reserved"] == 0 and snap["daily"]["used"] == 7.5


def test_limit_is_enforced_and_nothing_leaks_on_refusal(settings, learner_id):
    with session_scope() as session:
        usage.reserve(session, settings, learner_id, "audio_seconds", 100, "req-1")
        with pytest.raises(UsageLimitExceeded) as excinfo:
            usage.reserve(session, settings, learner_id, "audio_seconds", 30, "req-2")
        assert excinfo.value.scope == "daily"
        assert excinfo.value.remaining == 20
        snap = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
        assert snap["daily"]["reserved"] == 100  # the refused reservation left no trace
        assert snap["total"]["reserved"] == 100


def test_same_request_id_is_deduplicated(settings, learner_id):
    with session_scope() as session:
        first = usage.reserve(session, settings, learner_id, "model_calls", 1, "req-dup")
        again = usage.reserve(session, settings, learner_id, "model_calls", 1, "req-dup")
        assert again.deduplicated and again.id == first.id
        snap = usage.snapshot(session, settings, learner_id)["counters"]["model_calls"]
        assert snap["daily"]["reserved"] == 1


def test_concurrent_reservations_never_exceed_the_limit(settings, learner_id):
    """Twenty threads each try to reserve 10 of a 120 daily budget: at most 12 may succeed."""
    successes: list[int] = []
    failures: list[int] = []
    lock = threading.Lock()

    def worker(index: int) -> None:
        try:
            with session_scope() as session:
                usage.reserve(session, settings, learner_id, "audio_seconds", 10, f"req-par-{index}")
            with lock:
                successes.append(index)
        except UsageLimitExceeded:
            with lock:
                failures.append(index)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(successes) == 12
    assert len(failures) == 8
    with session_scope() as session:
        snap = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
        assert snap["daily"]["reserved"] == 120


def test_usage_endpoint_reports_empty_pricing_table(client, headers):
    payload = client.get("/usage", headers=headers).json()
    assert payload["pricing_table_entries"] == 0
    assert payload["estimated_cost"] is None
    assert set(payload["counters"]) == {"model_calls", "tokens", "audio_seconds"}
