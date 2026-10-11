"""Today (roadmap 4.1, D-33): GET /today only reads; opening Today (POST /today/prepare) keeps one unread episode
queued or ready and queues no second; the request's session commits before the response, so a failed commit is a
500 and never a 2xx; and every route shares one session per request."""
from __future__ import annotations

import importlib
import pkgutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select, update
from sqlalchemy.orm import Session

import dlp.api
from dlp.db.base import utcnow
from dlp.db.session import get_engine, get_session, session_scope
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner
from dlp.domains.identity.service import LAST_SEEN_EVERY, get_or_create_learner
from dlp.domains.jobs.models import Job
from dlp.domains.stories import service as stories
from dlp.domains.stories.models import StoryEpisode, StorySeries
from tests.conftest import auth_headers, open_today


def _count(model) -> int:
    with session_scope() as session:
        return session.scalar(select(func.count()).select_from(model))


def _writes_during(action) -> tuple[list, list[str]]:
    """What `action` returns, and every statement it sent that writes or locks a row."""
    statements: list[str] = []

    def record(_conn, _cursor, statement, _params, _context, _executemany):
        statements.append(statement)

    engine = get_engine()
    event.listen(engine, "before_cursor_execute", record)
    try:
        result = action()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return result, [statement for statement in statements
                    if statement.lstrip().split()[0].upper() in ("INSERT", "UPDATE", "DELETE")
                    or "FOR UPDATE" in statement.upper() or "FOR NO KEY UPDATE" in statement.upper()]


def test_get_today_never_writes_or_enqueues(client, headers):
    # the first request creates the learner; "last seen" is then fresh, so these reads write nothing at all
    assert client.get("/me", headers=headers).status_code == 200
    plans, writes = _writes_during(lambda: [client.get("/today", headers=headers) for _ in range(3)])
    assert all(plan.status_code == 200 for plan in plans)
    assert writes == [], writes
    # a learner with no series yet sees the series to come, and nothing is queued for them
    first = plans[0].json()
    assert first["series"]["episode_count"] == 0 and first["series"]["id"] is None
    assert first["series"]["title"] == "De Lindestraat" and first["series"]["cast"]
    assert first["episode"] is None and first["next_step"] == "explore"
    assert (_count(StorySeries), _count(StoryEpisode), _count(Job)) == (0, 0, 0)


def test_a_read_after_a_while_writes_only_last_seen(client, headers):
    """Like every signed-in request, a read refreshes "last seen" once it is LAST_SEEN_EVERY old; nothing else."""
    assert client.get("/me", headers=headers).status_code == 200
    with session_scope() as session:
        session.execute(update(Learner).values(last_seen_at=utcnow() - LAST_SEEN_EVERY - timedelta(minutes=1)))
    plan, writes = _writes_during(lambda: client.get("/today", headers=headers))
    assert plan.status_code == 200
    assert len(writes) == 1 and writes[0].lstrip().upper().startswith("UPDATE LEARNERS SET"), writes
    assert "last_seen_at" in writes[0]
    assert (_count(StorySeries), _count(StoryEpisode), _count(Job)) == (0, 0, 0)


def test_two_first_prepares_at_once_share_one_series_and_one_episode(database):
    """With "last seen" fresh, nothing serializes one learner's requests any more: two tabs opening Today for a
    learner without a series must both get the same plan, never a unique-index error."""
    with session_scope() as session:
        learner_id = get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com",
                                                              "Owner", "fixture", "two-tabs")).id
    barrier = Barrier(2)

    def prepare(_index):
        with session_scope() as session:
            learner = session.get(Learner, learner_id)
            barrier.wait(timeout=10)
            episode = stories.ensure_buffer(session, learner)
            return episode.id if episode is not None else None

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(prepare, [1, 2]))
    assert ids[0] is not None and ids[0] == ids[1]
    assert (_count(StorySeries), _count(StoryEpisode), _count(Job)) == (1, 1, 1)


def test_prepare_is_idempotent_and_queues_at_most_one_episode(client, headers):
    first = open_today(client, headers)
    second = open_today(client, headers)
    assert first["episode"]["status"] == "queued" and first["next_step"] == "wait"
    assert second["episode"]["id"] == first["episode"]["id"]
    assert second["series"]["episode_count"] == 1
    assert (_count(StoryEpisode), _count(Job)) == (1, 1)
    # the page's later reads show the same plan
    assert client.get("/today", headers=headers).json()["episode"]["id"] == first["episode"]["id"]
    # prepare is a write: without the fetch header (CSRF) it is refused
    plain = auth_headers()
    plain.pop("X-Requested-With")
    assert client.post("/today/prepare", headers=plain).status_code == 403


def test_commit_failure_reaches_the_client_as_500(database, monkeypatch):
    """The session commits before the response is sent (function scope), so a commit that fails is an error the
    learner sees, not a 200 whose writes were lost."""
    from dlp.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        headers = auth_headers()
        assert client.get("/me", headers=headers).status_code == 200

        def fail(self):
            raise RuntimeError("the commit failed")

        monkeypatch.setattr(Session, "commit", fail)
        response = client.post("/today/prepare", headers=headers)
    assert response.status_code == 500 and response.json()["detail"] == "internal error"
    monkeypatch.undo()
    assert (_count(StoryEpisode), _count(Job)) == (0, 0), "nothing of the failed request was kept"


def test_every_route_shares_one_function_scoped_session():
    """FastAPI caches a dependency per request by its scope too: a route asking for the session with another scope
    than `context_dep` would open a second session (a second transaction) in the same request."""
    scopes: list[str | None] = []

    def walk(dependant):
        for dependency in dependant.dependencies:
            if dependency.call is get_session:
                scopes.append(dependency.scope)
            walk(dependency)

    routes = 0
    for info in pkgutil.iter_modules(dlp.api.__path__):
        router = getattr(importlib.import_module(f"dlp.api.{info.name}"), "router", None)
        for route in getattr(router, "routes", []):
            if isinstance(route, APIRoute):
                routes += 1
                walk(route.dependant)
    assert routes > 80 and scopes and set(scopes) == {"function"}
