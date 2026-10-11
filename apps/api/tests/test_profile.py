"""The learner profile: one row, one level, the onboarding that queues the first episode."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from dlp.api.routes_me import reset_me
from dlp.db.session import session_scope
from dlp.domains.curriculum.models import CurriculumAttempt
from dlp.domains.identity.models import Learner
from dlp.domains.profile.models import LearnerProfile
from dlp.domains.stories.models import StoryEpisode, StorySeries
from tests.conftest import auth_headers, open_today


def _series_stage() -> str | None:
    with session_scope() as session:
        series = session.scalar(select(StorySeries))
        return None if series is None else series.stage_id


def test_me_returns_defaults_and_one_row_after_concurrent_calls(client, headers):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda i: client.get("/me", headers=auth_headers(f"me-request-{i}")), range(2)))
    assert [r.status_code for r in responses] == [200, 200]
    body = responses[0].json()
    assert body["profile"] == {
        "stage_id": "a1", "daily_goal_points": 20, "support_mode": None, "gloss_mode": "auto",
        "stated_goal": "", "onboarded_at": None, "earned_stage_id": None, "suggested_stage_id": None,
    }
    assert body["features"] == {}
    assert body["learner"]["email"] == "owner@example.com"
    with session_scope() as session:
        assert len(list(session.scalars(select(LearnerProfile)))) == 1


def test_patch_validates_and_keeps_other_fields(client, headers):
    assert client.patch("/me", json={"stage_id": "z9"}, headers=headers).status_code == 422
    assert client.patch("/me", json={"daily_goal_points": 25}, headers=headers).status_code == 422
    assert client.patch("/me", json={"nickname": "x"}, headers=headers).status_code == 422
    assert client.patch("/me", json={"stage_id": None}, headers=headers).status_code == 422
    assert client.patch("/me", json={"gloss_mode": None}, headers=headers).status_code == 422
    assert client.patch("/me", json={"support_mode": None}, headers=headers).status_code == 200
    first = client.patch("/me", json={"stage_id": "a2", "support_mode": "nl-fa"}, headers=headers).json()
    assert first["profile"]["stage_id"] == "a2" and first["profile"]["support_mode"] == "nl-fa"
    second = client.patch("/me", json={"daily_goal_points": 30}, headers=headers).json()["profile"]
    assert second == {**first["profile"], "daily_goal_points": 30}
    other = client.get("/me", headers=auth_headers("second-1", email="second@example.com")).json()["profile"]
    assert other["stage_id"] == "a1" and other["support_mode"] is None


def test_onboarding_runs_once_and_queues_one_episode(client, headers):
    body = {"support_mode": "nl-fa-en", "stage_id": "pre-a1", "daily_goal_points": 10, "stated_goal": "werk"}
    first = client.post("/me/onboarding", json=body, headers=headers)
    assert first.status_code == 200
    payload = first.json()
    assert payload["already_onboarded"] is False
    assert payload["profile"]["onboarded_at"] is not None
    assert payload["profile"]["stage_id"] == "pre-a1"
    assert payload["episode"] is not None and payload["episode"]["number"] == 1
    assert _series_stage() == "pre-a1"
    with session_scope() as session:
        assert len(list(session.scalars(select(StoryEpisode)))) == 1
    repeat = client.post("/me/onboarding", json={**body, "stage_id": "b1"}, headers=headers).json()
    assert repeat["already_onboarded"] is True
    assert repeat["profile"]["stage_id"] == "pre-a1"
    with session_scope() as session:
        assert len(list(session.scalars(select(StoryEpisode)))) == 1


def test_an_episode_queued_before_the_welcome_is_written_at_the_chosen_level(client, headers):
    open_today(client, headers)  # opening Today before the welcome queues episode one at the default level
    with session_scope() as session:
        assert [row.stage_id for row in session.scalars(select(StoryEpisode))] == ["a1"]
    body = {"support_mode": "nl-en", "stage_id": "b1", "daily_goal_points": 20}
    payload = client.post("/me/onboarding", json=body, headers=headers).json()
    assert payload["episode"]["number"] == 1
    with session_scope() as session:
        episodes = list(session.scalars(select(StoryEpisode)))
        assert [row.stage_id for row in episodes] == ["b1"], "still queued, so it follows the chosen level"
        assert episodes[0].theme_source == "auto"


def test_stage_is_shared_with_the_serial_in_both_directions(client, headers):
    open_today(client, headers)
    assert client.patch("/me", json={"stage_id": "a2"}, headers=headers).status_code == 200
    assert _series_stage() == "a2"
    assert client.post("/stories/level", json={"stage_id": "b1"}, headers=headers).status_code == 200
    assert client.get("/me", headers=headers).json()["profile"]["stage_id"] == "b1"
    assert client.post("/stories/level", json={"stage_id": "nope"}, headers=headers).status_code == 404


def test_a_learner_with_a_serial_keeps_its_level_when_the_profile_is_created(client, headers):
    assert client.post("/stories/level", json={"stage_id": "b1"}, headers=headers).status_code == 200
    with session_scope() as session:
        for row in session.scalars(select(LearnerProfile)):
            session.delete(row)
    assert _series_stage() == "b1"
    assert client.get("/me", headers=headers).json()["profile"]["stage_id"] == "b1"


def test_reset_undoes_onboarding_outside_production(client, headers):
    client.post("/me/onboarding", json={"support_mode": "nl-en", "stage_id": "a2"}, headers=headers)
    profile = client.post("/me/reset", headers=headers).json()["profile"]
    assert profile["onboarded_at"] is None and profile["stage_id"] == "a1" and profile["support_mode"] is None


def _pass(*stages: str) -> None:
    """Record passed final checks for the owner, as the curriculum does after a successful attempt."""
    with session_scope() as session:
        learner = session.scalar(select(Learner).where(Learner.email == "owner@example.com"))
        assert learner is not None
        for stage in stages:
            session.add(CurriculumAttempt(learner_id=learner.id, stage_id=stage, request_id=f"pass-{stage}",
                                          status="passed", content_version="test", test_snapshot={}))


def _offer(client, headers) -> tuple[str | None, str | None]:
    profile = client.get("/me", headers=headers).json()["profile"]
    return profile["earned_stage_id"], profile["suggested_stage_id"]


def test_passing_the_current_stage_offers_the_next_one_without_moving(client, headers):
    assert client.patch("/me", json={"stage_id": "a1"}, headers=headers).status_code == 200
    assert _offer(client, headers) == (None, None)
    _pass("a1")
    assert _offer(client, headers) == ("a1", "pre-a2")
    assert client.get("/me", headers=headers).json()["profile"]["stage_id"] == "a1", "an offer is never applied"


def test_a_self_placed_learner_is_offered_the_stage_after_the_one_passed(client, headers):
    client.patch("/me", json={"stage_id": "b1"}, headers=headers)
    _pass("b1")
    assert _offer(client, headers) == ("b1", "pre-b2")


def test_passing_only_a_lower_stage_offers_nothing(client, headers):
    client.patch("/me", json={"stage_id": "a1"}, headers=headers)
    _pass("pre-a1")
    assert _offer(client, headers) == (None, None)


def test_passing_a_higher_stage_offers_the_stage_after_it(client, headers):
    client.patch("/me", json={"stage_id": "a1"}, headers=headers)
    _pass("a2")
    assert _offer(client, headers) == ("a2", "pre-b1")


def test_reset_is_refused_in_production(settings):
    # in production the fixture sign-in is refused before any route runs, so the guard is called directly
    production = settings.model_copy(update={"app_env": "production"})
    with pytest.raises(HTTPException) as refused:
        reset_me(ctx=None, settings=production, session=None)  # type: ignore[arg-type]
    assert refused.value.status_code == 404


def test_reset_brings_the_serial_back_with_the_profile(client, headers):
    client.post("/me/onboarding", json={"support_mode": "nl-en", "stage_id": "b1"}, headers=headers)
    assert _series_stage() == "b1"
    profile = client.post("/me/reset", headers=headers).json()["profile"]
    assert _series_stage() == profile["stage_id"] == "a1"


def test_the_daily_goal_from_the_profile_is_the_goal_on_today(client, headers):
    client.patch("/me", json={"daily_goal_points": 10}, headers=headers)
    goal = client.get("/today", headers=headers).json()["goal"]
    assert goal["target"] == 10 and goal["met"] is False


def test_the_reason_is_one_of_the_offered_choices(client, headers):
    assert client.patch("/me", json={"stated_goal": "werk"}, headers=headers).status_code == 200
    assert client.patch("/me", json={"stated_goal": "iets anders"}, headers=headers).status_code == 422
    body = {"support_mode": "nl-en", "stage_id": "a1", "stated_goal": "x" * 20}
    assert client.post("/me/onboarding", json=body, headers=headers).status_code == 422


def test_the_export_carries_the_profile_and_its_switches(client, headers):
    profile = client.get("/export", headers=headers).json()["profile"]
    assert profile["stage_id"] and profile["features"] == {}

