"""Real PostgreSQL transaction tests: session JSON changes must not clobber each other."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.content.service import get_mission
from dlp.domains.identity.assertions import Principal
from dlp.domains.identity.models import Learner
from dlp.domains.identity.service import get_or_create_learner
from dlp.domains.practice.models import PracticeSession
from dlp.domains.practice.service import get_session_for_learner, start_session


def test_first_visit_concurrent_identity_requests_share_one_learner(database):
    barrier = Barrier(2)

    def create(index):
        with session_scope() as session:
            barrier.wait(timeout=10)
            return get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com",
                                                           "Owner", "fixture", f"first-visit-{index}")).id

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(create, [1, 2]))
    assert ids[0] == ids[1]
    with session_scope() as session:
        assert len(list(session.scalars(select(Learner)))) == 1


def test_simultaneous_starts_create_only_one_session(database):
    with session_scope() as session:
        learner = get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com",
                                                         "Owner", "fixture", "race-start"))
        learner_id = learner.id
    barrier = Barrier(2)

    def start(index):
        with session_scope() as session:
            mission = get_mission(session, "appointment-change")
            barrier.wait(timeout=10)
            return start_session(session, learner_id=learner_id, mission=mission, variant="base",
                                 request_id=f"concurrent-start-{index}").id

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(start, [1, 2]))
    assert ids[0] == ids[1]
    with session_scope() as session:
        assert len(list(session.scalars(select(PracticeSession)))) == 1


def test_locked_state_updates_preserve_both_changes(database):
    with session_scope() as session:
        learner = get_or_create_learner(session, Principal("fixture:owner@example.com", "owner@example.com",
                                                         "Owner", "fixture", "race-state"))
        learner_id = learner.id
        practice_id = start_session(session, learner_id=learner_id, mission=get_mission(session, "appointment-change"),
                                    variant="base", request_id="state-start").id
    barrier = Barrier(2)

    def update(key):
        with session_scope() as session:
            # Simulate both requests having an old ORM object before either locks it.
            stale = session.get(PracticeSession, practice_id)
            assert stale is not None
            barrier.wait(timeout=10)
            practice = get_session_for_learner(session, learner_id, practice_id, for_update=True)
            practice.state = {**practice.state, key: True}

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(update, ["answer_saved", "hint_saved"]))
    with session_scope() as session:
        state = session.get(PracticeSession, practice_id).state
        assert state["answer_saved"] and state["hint_saved"]
