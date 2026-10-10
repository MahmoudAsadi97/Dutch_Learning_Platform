"""The activity service: one event per countable action, points once, the day equal to its events."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier

import pytest
from sqlalchemy import func, select

from dlp.db.session import session_scope
from dlp.domains.activity import rules
from dlp.domains.activity.day import local_today
from dlp.domains.activity.models import ActivityEvent, LearningDay
from dlp.domains.activity.service import add_to_day, reached, record_activity
from dlp.domains.identity.models import Learner
from dlp.domains.profile.models import LearnerProfile


def _learner(email: str) -> str:
    with session_scope() as session:
        learner = Learner(subject=f"fixture:{email}", email=email)
        session.add(learner)
        session.flush()
        return learner.id


def _day(learner_id, day: date | None = None) -> LearningDay | None:
    with session_scope() as session:
        return session.scalar(select(LearningDay).where(LearningDay.learner_id == learner_id,
                                                        LearningDay.day == (day or local_today())))


def test_the_same_action_from_two_requests_at_once_awards_once(database):
    learner_id = _learner("race-activity@example.com")
    barrier = Barrier(2)

    def read(_index):
        with session_scope() as session:
            barrier.wait(timeout=10)
            return record_activity(session, learner_id, kind="episode_read", ref="episode-1")

    with ThreadPoolExecutor(max_workers=2) as executor:
        awards = list(executor.map(read, [1, 2]))
    assert sorted(award.points for award in awards) == [0, 10]
    assert sorted(award.recorded for award in awards) == [False, True]
    row = _day(learner_id)
    assert row is not None and row.points == 10 and row.episodes_read == 1


def test_a_retried_request_pays_nothing_and_a_new_one_pays_again(database):
    learner_id = _learner("retry-activity@example.com")
    with session_scope() as session:
        first = record_activity(session, learner_id, kind="word_review", ref="word-1", request_id="review-0001")
        again = record_activity(session, learner_id, kind="word_review", ref="word-1", request_id="review-0001")
        later = record_activity(session, learner_id, kind="word_review", ref="word-1", request_id="review-0002")
    assert (first.points, again.points, later.points) == (1, 0, 1)
    assert not again.recorded
    row = _day(learner_id)
    assert row.points == 2 and row.words_reviewed == 2


def test_a_per_request_action_needs_the_request_id(database):
    learner_id = _learner("no-request-id@example.com")
    with session_scope() as session, pytest.raises(ValueError):
        record_activity(session, learner_id, kind="word_review", ref="word-1")


def test_a_daily_action_counts_again_on_the_next_brussels_day(database, monkeypatch):
    monkeypatch.setitem(rules.RULES, "daily_check", rules.Rule(points=4, counter=None, skill=None, scope="per_day"))
    learner_id = _learner("daily-activity@example.com")
    late = datetime(2026, 10, 9, 21, 30, tzinfo=UTC)  # 23:30 in Brussels
    after_midnight = datetime(2026, 10, 9, 22, 30, tzinfo=UTC)  # 00:30 on the 10th in Brussels
    with session_scope() as session:
        awards = [record_activity(session, learner_id, kind="daily_check", ref="warm-up", now=moment).points
                  for moment in (late, late, after_midnight)]
    assert awards == [4, 0, 4]
    assert _day(learner_id, date(2026, 10, 9)).points == 4
    assert _day(learner_id, date(2026, 10, 10)).points == 4


def test_an_action_without_units_is_recorded_but_moves_no_day(database):
    learner_id = _learner("zero-activity@example.com")
    with session_scope() as session:
        none_right = record_activity(session, learner_id, kind="episode_questions", ref="episode-2", units=0)
        replay = record_activity(session, learner_id, kind="episode_questions", ref="episode-2", units=3)
    assert none_right.recorded and none_right.points == 0
    assert not replay.recorded and replay.points == 0, "answering again cannot earn the points later"
    assert _day(learner_id) is None


def test_a_day_holds_exactly_the_points_of_its_events(database):
    learner_id = _learner("sum-activity@example.com")
    with session_scope() as session:
        record_activity(session, learner_id, kind="episode_read", ref="episode-3")
        record_activity(session, learner_id, kind="episode_questions", ref="episode-3", units=2)
        record_activity(session, learner_id, kind="episode_choice", ref="episode-3")
        record_activity(session, learner_id, kind="read_aloud", ref="episode-3:0")
        record_activity(session, learner_id, kind="video_watched", ref="video-1")
        record_activity(session, learner_id, kind="video_questions", ref="video-1", units=1)
        record_activity(session, learner_id, kind="word_review", ref="word-9", request_id="review-0009")
        total = session.scalar(select(func.sum(ActivityEvent.points)).where(ActivityEvent.learner_id == learner_id,
                                                                            ActivityEvent.day == local_today()))
    row = _day(learner_id)
    assert row.points == total == 10 + 6 + 2 + 5 + 10 + 3 + 1
    assert (row.episodes_read, row.questions_correct, row.read_aloud, row.videos_watched, row.words_reviewed) == \
        (1, 3, 1, 1, 1)


def test_the_day_keeps_the_goal_it_was_played_against(database):
    learner_id = _learner("goal-activity@example.com")
    with session_scope() as session:
        session.add(LearnerProfile(learner_id=learner_id, daily_goal_points=30))
        session.flush()
        record_activity(session, learner_id, kind="episode_read", ref="episode-4")
        record_activity(session, learner_id, kind="video_watched", ref="video-4")
    row = _day(learner_id)
    assert row.goal_target == 30 and row.points == 20 and not row.goal_met
    with session_scope() as session:
        record_activity(session, learner_id, kind="video_questions", ref="video-4", units=4)
    row = _day(learner_id)
    assert row.points == 32 and row.goal_met


def test_unknown_kinds_and_counters_are_refused(database):
    learner_id = _learner("unknown-activity@example.com")
    with session_scope() as session:
        with pytest.raises(KeyError):
            record_activity(session, learner_id, kind="episode_skimmed", ref="episode-5")
        with pytest.raises(ValueError):
            add_to_day(session, learner_id, day=local_today(), points=1, counts={"episodes_skimmed": 1})


def test_every_rule_moves_a_real_day_counter():
    for kind, rule in rules.RULES.items():
        assert rule.counter is None or rule.counter in rules.COUNTERS, kind
        assert rule.counter is None or hasattr(LearningDay, rule.counter), kind
        assert rule.skill in (None, "reading", "listening", "speaking", "writing"), kind
        assert rule.points >= 0, kind


@pytest.mark.parametrize(("moment", "day"), [
    (datetime(2026, 10, 9, 21, 30, tzinfo=UTC), date(2026, 10, 9)),  # 23:30 summer time
    (datetime(2026, 10, 9, 22, 30, tzinfo=UTC), date(2026, 10, 10)),  # 00:30 summer time
    (datetime(2026, 10, 25, 22, 30, tzinfo=UTC), date(2026, 10, 25)),  # 23:30 on the night summer time ends
    (datetime(2026, 10, 25, 23, 30, tzinfo=UTC), date(2026, 10, 26)),  # 00:30 winter time
    (datetime(2026, 3, 28, 22, 30, tzinfo=UTC), date(2026, 3, 28)),  # 23:30 winter time
    (datetime(2026, 3, 29, 22, 30, tzinfo=UTC), date(2026, 3, 30)),  # 00:30 after summer time began
])
def test_the_learner_day_follows_the_brussels_calendar(moment, day):
    assert local_today(moment) == day


def test_changing_the_goal_applies_to_today_so_its_dot_matches_what_today_showed(client, headers):
    assert client.get("/me", headers=headers).status_code == 200
    with session_scope() as session:
        learner_id = session.scalar(select(Learner.id).where(Learner.email == "owner@example.com"))
        record_activity(session, learner_id, kind="episode_read", ref="episode-6")
        record_activity(session, learner_id, kind="video_watched", ref="video-6")
    assert _day(learner_id).goal_met, "20 points meet the default goal of 20"
    assert client.patch("/me", json={"daily_goal_points": 30}, headers=headers).status_code == 200
    row = _day(learner_id)
    assert (row.goal_target, row.goal_met) == (30, False)
    plan = client.get("/today", headers=headers).json()
    assert plan["goal"]["points"] == 20 and plan["goal"]["target"] == 30


def test_only_the_award_that_crosses_the_goal_reports_it(database):
    learner_id = _learner("crossing-activity@example.com")
    with session_scope() as session:
        below = record_activity(session, learner_id, kind="episode_read", ref="episode-7")
        crossing = record_activity(session, learner_id, kind="video_watched", ref="video-7")
        beyond = record_activity(session, learner_id, kind="episode_choice", ref="episode-7")
        repeat = record_activity(session, learner_id, kind="video_watched", ref="video-7")
    assert [award.goal_reached for award in (below, crossing, beyond, repeat)] == [False, True, False, False]
    assert reached(below, None, crossing) == {"goal_reached": True}
    assert reached(below, beyond) == {}


def test_a_long_request_id_is_kept_and_its_retry_repeats_the_goal(client, headers):
    """The request bodies allow 80 characters; the response that crossed the goal may never have arrived."""
    saved = client.post("/words", headers=headers, json={"term": "de buurvrouw", "meaning_en": "neighbour"}).json()
    item_id = saved["item"]["id"]
    with session_scope() as session:
        learner_id = session.scalar(select(Learner.id).where(Learner.email == "owner@example.com"))
        add_to_day(session, learner_id, day=local_today(), points=19)
    request_id = "r" * 80
    review = {"request_id": request_id, "grade": "good"}
    first = client.post(f"/words/{item_id}/review", headers=headers, json=review)
    assert first.status_code == 200, first.text
    assert first.json()["goal_reached"] is True
    retried = client.post(f"/words/{item_id}/review", headers=headers, json=review).json()
    assert retried.get("goal_reached") is True, "the retry says what the lost response said"
    later = client.post(f"/words/{item_id}/review", headers=headers, json={"request_id": "r" * 79, "grade": "good"})
    assert "goal_reached" not in later.json(), "only the crossing request repeats it"
    with session_scope() as session:
        event = session.scalar(select(ActivityEvent).where(ActivityEvent.request_id == request_id))
        assert event is not None and event.meta == {"goal_reached": True}
    assert _day(learner_id).points == 21
