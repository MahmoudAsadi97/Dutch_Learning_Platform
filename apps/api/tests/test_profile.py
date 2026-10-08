"""The learner profile: one row, one level, the onboarding that queues the first episode."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.profile.models import LearnerProfile
from dlp.domains.stories.models import StoryEpisode, StorySeries
from tests.conftest import auth_headers


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
        "stated_goal": "", "onboarded_at": None, "suggested_stage_id": None,
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


def test_stage_is_shared_with_the_serial_in_both_directions(client, headers):
    client.get("/today", headers=headers)
    assert client.patch("/me", json={"stage_id": "a2"}, headers=headers).status_code == 200
    assert _series_stage() == "a2"
    assert client.post("/stories/level", json={"stage_id": "b1"}, headers=headers).status_code == 200
    assert client.get("/me", headers=headers).json()["profile"]["stage_id"] == "b1"
    assert client.post("/stories/level", json={"stage_id": "nope"}, headers=headers).status_code == 404


def test_reset_undoes_onboarding_outside_production(client, headers):
    client.post("/me/onboarding", json={"support_mode": "nl-en", "stage_id": "a2"}, headers=headers)
    profile = client.post("/me/reset", headers=headers).json()["profile"]
    assert profile["onboarded_at"] is None and profile["stage_id"] == "a1" and profile["support_mode"] is None
