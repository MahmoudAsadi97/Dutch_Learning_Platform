"""The story engine: validated generation ahead of the learner, idempotent learner actions, the word bank with
spaced repetition, and the daily plan. Fixture providers prove plumbing; language quality is a human's job."""
from __future__ import annotations

import json
import uuid
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from dlp.api.deps import providers_dep
from dlp.config import get_settings
from dlp.db.session import session_scope
from dlp.domains.identity.models import Learner
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.service import drain
from dlp.domains.stories import service, today, vocab
from dlp.domains.stories.bible import DEFAULT_BIBLE, PROFILES, profile_for
from dlp.domains.stories.models import LearningDay, StoryEpisode, StorySeries, VocabItem
from dlp.domains.stories.schemas import EpisodeDraft
from dlp.domains.stories.validator import coverage, feedback_text, lemma_key, tokens, validate_draft
from dlp.domains.usage.models import UsageCounter
from dlp.providers.fixtures import FixtureChatModel, FixtureSpeechToText
from dlp.providers.registry import get_providers

from .conftest import FIXTURES, auth_headers

GOOD = json.loads((FIXTURES / "chat_replies.json").read_text(encoding="utf-8"))["story-episode-v1"]["default"]


@pytest.fixture(autouse=True)
def story_allowance(monkeypatch):
    """An episode costs a few thousand tokens; the shared test limit is sized for short rubric calls."""
    monkeypatch.setattr(get_settings(), "usage_daily_tokens", 40_000)
    monkeypatch.setattr(get_settings(), "usage_total_tokens", 400_000)
A1 = profile_for("a1")
CAST = frozenset(c["name"] for c in DEFAULT_BIBLE["cast"])


def allowed_a1() -> frozenset[str]:
    return frozenset(w for key in service.stage_vocabulary("a1") for w in key.split())


def draft(**changes) -> EpisodeDraft:
    data = deepcopy(GOOD)
    data.update(changes)
    return EpisodeDraft.model_validate(data)


# --- validator ---------------------------------------------------------------------------------------------

def test_fixture_episode_passes_the_a1_gate_with_known_vocabulary():
    result = validate_draft(draft(), A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert result.ok and not result.warnings, result.as_dict()
    assert result.metrics["coverage"] > 0.9 and result.metrics["longest_sentence"] <= A1.max_sentence_words


def test_english_text_is_rejected_as_not_dutch():
    english = draft(paragraphs=["This is a story about Sami and the key that he lost in the morning. " * 3] * 3)
    result = validate_draft(english, A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert any(item.startswith("not_dutch") for item in result.hard)


def test_question_evidence_must_be_copied_from_the_story():
    questions = deepcopy(GOOD["questions"])
    questions[1]["evidence"] = "Baas heeft de sleutel in zijn bed verstopt."
    result = validate_draft(draft(questions=questions), A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert "question_1_evidence_missing" in result.hard


def test_a_draft_far_below_the_length_floor_is_rewritten_with_an_instruction():
    short = draft(paragraphs=["Sami zoekt zijn sleutel.", "Baas heeft de sleutel.", "Sami lacht."],
                  paragraphs_en=["Sami looks for his key.", "Baas has the key.", "Sami laughs."])
    result = validate_draft(short, A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert any(item.startswith("word_count") for item in result.hard)
    text = feedback_text(result, A1)
    assert "minstens 60" in text and "dialoog" in text and "FAILED CHECKS" in text


def test_vocabulary_far_above_level_and_long_sentences_are_hard_failures():
    hard = draft(paragraphs=[
        "De gemeenteraad bekrachtigde gisteren de omstreden herbestemming van het voormalige slachthuis nadat de "
        "oppositie tevergeefs om uitstel had verzocht, ondanks de verontwaardiging van de omwonenden.",
        "Sami overwoog een bezwaarschrift in te dienen, maar de termijn bleek inmiddels verstreken te zijn volgens de "
        "ambtenaar, die hem vriendelijk doch beslist naar het loket verwees.",
        "Ayşe haalde haar schouders op.",
    ])
    result = validate_draft(hard, A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert any(item.startswith("vocabulary_too_hard") for item in result.hard)
    assert any(item.startswith("sentence_too_long") for item in result.hard)


def test_regional_gij_needs_a_glossary_label():
    paragraphs = deepcopy(GOOD["paragraphs"])
    paragraphs[1] = paragraphs[1].replace("Wil je brood?", "Wilt gij brood?")
    result = validate_draft(draft(paragraphs=paragraphs), A1, allowed_vocabulary=allowed_a1(), cast_names=CAST)
    assert any(item.startswith("regional_form") for item in result.hard)
    glossary = deepcopy(GOOD["glossary"]) + [{"term": "gij", "meaning_en": "you (regional, informal)",
                                               "meaning_fa": "تو (گویشی)", "example": "Wilt gij brood?"}]
    labelled = validate_draft(draft(paragraphs=paragraphs, glossary=glossary), A1, allowed_vocabulary=allowed_a1(),
                              cast_names=CAST)
    assert not any(item.startswith("regional_form") for item in labelled.hard)


def test_inflections_compounds_and_names_count_as_known():
    share, unknown = coverage(tokens("Sami koopt appels en zoekt de fietsenwinkel. Ayşe lacht."),
                              frozenset({"kopen", "appel", "fiets", "winkel", "zoeken", "lachen", "sami", "ayşe"}))
    assert unknown == [] and share == 1.0
    assert lemma_key("de toonbank") == "toonbank" and lemma_key("zich haasten") == "haasten"


def test_every_stage_has_a_profile_in_order():
    assert list(PROFILES) == ["pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1", "pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2"]
    assert all(PROFILES[a].max_words <= PROFILES[b].max_words for a, b in zip(list(PROFILES), list(PROFILES)[1:], strict=False))


# --- spaced repetition and streak ----------------------------------------------------------------------------

def test_sm2_schedule_grows_on_good_answers_and_returns_quickly_on_a_lapse():
    item = VocabItem(key="toonbank", term="de toonbank", due_at=datetime.now(UTC))
    now = datetime(2026, 10, 2, 9, 0, tzinfo=UTC)
    vocab.schedule(item, "good", now=now)
    assert item.interval_days == 1 and item.repetitions == 1 and item.due_at == now + timedelta(days=1)
    vocab.schedule(item, "good", now=now)
    assert item.interval_days == 6
    vocab.schedule(item, "easy", now=now)
    assert item.interval_days >= 15 and item.ease > 2.5
    vocab.schedule(item, "again", now=now)
    assert item.repetitions == 0 and item.lapses == 1 and item.due_at == now + timedelta(minutes=10)
    for _ in range(10):
        vocab.schedule(item, "hard", now=now)
    assert item.ease >= 1.3


def test_streak_counts_consecutive_days_and_tolerates_an_unstarted_today(database):
    with session_scope() as session:
        learner = Learner(subject="fixture:streak@example.com", email="streak@example.com")
        session.add(learner)
        session.flush()
        today_date = date(2026, 10, 2)
        for offset in (1, 2, 3, 6, 7):
            today.add_points(session, learner.id, points=5, day=today_date - timedelta(days=offset))
        run = today.streak(session, learner.id, today_date=today_date)
        assert run == {"current": 3, "best": 3, "today_active": False, "today_points": 0, "active_days": 5}
        today.add_points(session, learner.id, points=25, day=today_date)
        run = today.streak(session, learner.id, today_date=today_date)
        assert run["current"] == 4 and run["today_active"] and run["today_points"] == 25
        row = session.scalar(select(LearningDay).where(LearningDay.learner_id == learner.id, LearningDay.day == today_date))
        assert row.goal_met is True


# --- generation ---------------------------------------------------------------------------------------------

def _learner(session) -> Learner:
    learner = session.scalar(select(Learner).where(Learner.email == "owner@example.com"))
    assert learner is not None
    return learner


def test_today_queues_an_episode_and_the_job_writes_a_validated_one(client, headers):
    first = client.get("/today", headers=headers).json()
    assert first["episode"]["status"] == "queued" and first["next_step"] == "wait"
    assert first["series"]["title"] == "De Lindestraat" and first["series"]["stage_id"] == "a1"
    assert first["streak"]["current"] == 0 and first["goal"] == {"target": 20, "points": 0, "met": False}
    assert client.get("/today", headers=headers).json()["series"]["episode_count"] == 1, "no second queue while one is pending"
    assert drain(get_settings()) == 1
    plan = client.get("/today", headers=headers).json()
    episode = plan["episode"]
    assert episode["status"] == "ready" and plan["next_step"] == "read"
    assert episode["title"] == GOOD["title"] and len(episode["paragraphs"]) == 4
    assert all("answer_index" not in question for question in episode["questions"]), "answers stay on the server"
    assert episode["provider"] == "fixture" and episode["content_status"] == "generated"
    assert episode["topic_id"].startswith("a1-t") and episode["theme"]
    with session_scope() as session:
        row = session.get(StoryEpisode, uuid.UUID(episode["id"]))
        assert row.checks["ok"] and row.attempts == 1 and row.word_count == 127
        series = session.get(StorySeries, row.series_id)
        assert series.memory[-1]["number"] == 1 and "sleutel" in series.memory[-1]["recap"]
        calls = session.scalar(select(UsageCounter).where(UsageCounter.metric == "model_calls",
                                                          UsageCounter.scope == "daily"))
        assert calls.used == 1 and calls.reserved == 0


def test_a_draft_that_fails_the_gate_is_rewritten_once_with_feedback(client, headers):
    bad = deepcopy(GOOD)
    bad["questions"][0]["evidence"] = "Deze zin staat niet in het verhaal."
    table = {"story-episode-v1": {"rules": [{"any": ["FAILED CHECKS"], "reply": GOOD}], "default": bad}}
    writer = FixtureChatModel(table)
    client.get("/today", headers=headers)
    with session_scope() as session:
        episode = session.scalar(select(StoryEpisode))
        result = service.generate_episode(session, {"episode_id": str(episode.id)}, get_settings(),
                                          replace(get_providers(), chat_strong=writer))
    assert result == {"status": "ready", "attempts": 2}
    assert len(writer.calls) == 2 and "question_0_evidence_missing" in writer.calls[1]["messages"][-1]


def test_a_persistently_bad_draft_fails_honestly_and_can_be_retried(client, headers):
    bad = deepcopy(GOOD)
    bad["paragraphs"] = ["The council approved the plan after a long debate about the budget and the station."] * 3
    writer = FixtureChatModel({"story-episode-v1": bad})
    client.get("/today", headers=headers)
    with session_scope() as session:
        episode = session.scalar(select(StoryEpisode))
        result = service.generate_episode(session, {"episode_id": str(episode.id)}, get_settings(),
                                          replace(get_providers(), chat_strong=writer))
        episode_id = episode.id
    assert result["status"] == "failed" and len(writer.calls) == 2
    plan = client.get("/today", headers=headers).json()
    assert plan["episode"] is None or plan["episode"]["id"] != str(episode_id)
    assert plan["failed"]["error_code"] == "quality" and isinstance(plan["failed"]["warnings"], list)
    retry = client.post(f"/stories/episodes/{episode_id}/retry", headers=headers)
    assert retry.status_code == 202 and retry.json()["status"] == "queued"
    with session_scope() as session:
        assert session.scalar(select(Job).where(Job.status == "queued")) is not None


def test_a_provider_failure_keeps_the_reservation_and_marks_the_episode(client, headers):
    writer = FixtureChatModel({"story-episode-v1": GOOD}, fail_first=1)
    client.get("/today", headers=headers)
    with session_scope() as session:
        episode = session.scalar(select(StoryEpisode))
        result = service.generate_episode(session, {"episode_id": str(episode.id)}, get_settings(),
                                          replace(get_providers(), chat_strong=writer))
    assert result["status"] == "failed"
    with session_scope() as session:
        episode = session.scalar(select(StoryEpisode))
        assert episode.error_code == "provider"
        calls = session.scalar(select(UsageCounter).where(UsageCounter.metric == "model_calls", UsageCounter.scope == "daily"))
        assert calls.used >= 1 and calls.reserved == 0


def test_an_exhausted_allowance_fails_without_a_model_call(client, headers, monkeypatch):
    monkeypatch.setattr(get_settings(), "usage_daily_model_calls", 0)
    writer = FixtureChatModel({"story-episode-v1": GOOD})
    client.get("/today", headers=headers)
    with session_scope() as session:
        episode = session.scalar(select(StoryEpisode))
        result = service.generate_episode(session, {"episode_id": str(episode.id)}, get_settings(),
                                          replace(get_providers(), chat_strong=writer))
    assert result["status"] == "failed" and not writer.calls
    with session_scope() as session:
        assert session.scalar(select(StoryEpisode)).error_code == "allowance"


# --- learner actions ------------------------------------------------------------------------------------------

def ready_episode(client, headers) -> dict:
    client.get("/today", headers=headers)
    drain(get_settings())
    return client.get("/today", headers=headers).json()["episode"]


def test_answers_are_graded_once_and_the_choice_queues_the_next_episode(client, headers):
    episode = ready_episode(client, headers)
    eid = episode["id"]
    wrong = client.post(f"/stories/episodes/{eid}/answers", headers=headers,
                        json={"request_id": "ans-1", "answers": {"0": 1}})
    assert wrong.status_code == 422
    graded = client.post(f"/stories/episodes/{eid}/answers", headers=headers,
                         json={"request_id": "ans-1", "answers": {"0": 1, "1": 2, "2": 1}}).json()
    assert graded["answered"] and [q["correct"] for q in graded["questions"]] == [True, True, False]
    assert graded["questions"][2]["evidence"] == "Hij wil een koekje." and graded["read_at"]
    again = client.post(f"/stories/episodes/{eid}/answers", headers=headers,
                        json={"request_id": "ans-1", "answers": {"0": 1, "1": 2, "2": 1}})
    assert again.status_code == 200, "a retry with the same request id is answered from the stored result"
    other = client.post(f"/stories/episodes/{eid}/answers", headers=headers,
                        json={"request_id": "ans-2", "answers": {"0": 1, "1": 2, "2": 0}})
    assert other.status_code == 409, "the questions cannot be re-answered for more points"
    plan = client.get("/today", headers=headers).json()
    assert plan["goal"]["points"] == 10 + 2 * 3 and plan["streak"]["current"] == 1 and plan["streak"]["today_active"]
    assert plan["episode"] is None and plan["awaiting_choice"]["id"] == eid and plan["next_step"] == "choose"

    chosen = client.post(f"/stories/episodes/{eid}/choice", headers=headers, json={"choice": "b"}).json()
    assert chosen["chosen_choice"] == "b"
    library = client.get("/stories", headers=headers).json()
    assert library["series"]["episode_count"] == 2 and [item["number"] for item in library["items"]] == [2, 1]
    assert library["items"][0]["status"] == "queued"
    with session_scope() as session:
        queued = session.scalar(select(StoryEpisode).where(StoryEpisode.number == 2))
        assert queued.previous_choice == GOOD["choices"][1]["label"]
        series = session.get(StorySeries, queued.series_id)
        assert series.memory[0]["choice"] == GOOD["choices"][1]["label"]
    assert client.get("/today", headers=headers).json()["goal"]["points"] == 18
    assert client.post(f"/stories/episodes/{eid}/rating", headers=headers, json={"rating": 1}).json()["rating"] == 1
    bad_choice = client.post(f"/stories/episodes/{eid}/choice", headers=headers, json={"choice": "c"})
    assert bad_choice.status_code == 422


def test_marking_read_awards_points_once(client, headers):
    episode = ready_episode(client, headers)
    client.post(f"/stories/episodes/{episode['id']}/read", headers=headers)
    client.post(f"/stories/episodes/{episode['id']}/read", headers=headers)
    assert client.get("/today", headers=headers).json()["goal"]["points"] == 10


def test_a_learner_cannot_see_or_touch_another_learners_episode(client, headers):
    episode = ready_episode(client, headers)
    other = auth_headers("other-request", email="second@example.com")
    assert client.get(f"/stories/episodes/{episode['id']}", headers=other).status_code == 404
    assert client.post(f"/stories/episodes/{episode['id']}/read", headers=other).status_code == 404
    theirs = client.get("/stories", headers=other).json()
    assert theirs["series"]["episode_count"] == 0 and theirs["items"] == [], "a series of their own, nothing shared"
    assert client.get("/today", headers=other).json()["series"]["episode_count"] == 1


def test_level_can_be_changed_and_a_wish_queues_a_themed_episode(client, headers):
    assert client.post("/stories/level", headers=headers, json={"stage_id": "a2"}).json()["stage_id"] == "a2"
    assert client.post("/stories/level", headers=headers, json={"stage_id": "z9"}).status_code == 404
    wished = client.post("/stories/episodes", headers=headers, json={"request_id": "wish-1", "theme": "over voetbal"})
    assert wished.status_code == 202 and wished.json()["theme"] == "over voetbal" and wished.json()["theme_source"] == "learner"
    same = client.post("/stories/episodes", headers=headers, json={"request_id": "wish-1", "theme": "over voetbal"})
    assert same.json()["id"] == wished.json()["id"], "a retried wish does not queue twice"
    client.post("/stories/episodes", headers=headers, json={"request_id": "wish-2", "theme": "de markt"})
    third = client.post("/stories/episodes", headers=headers, json={"request_id": "wish-3", "theme": "de bus"})
    assert third.status_code == 409, "at most two unread episodes are written ahead"
    with session_scope() as session:
        assert {row.stage_id for row in session.scalars(select(StoryEpisode))} == {"a2"}


def test_glossary_words_enter_the_word_bank_and_come_back_when_due(client, headers):
    episode = ready_episode(client, headers)
    saved = client.post(f"/stories/episodes/{episode['id']}/words", headers=headers, json={"term": "de toonbank"}).json()
    assert saved["created"] and saved["item"]["meaning_fa"] == "پیشخوان" and saved["item"]["due"]
    repeat = client.post(f"/stories/episodes/{episode['id']}/words", headers=headers, json={"term": "toonbank"})
    assert repeat.json()["created"] is False
    assert client.post(f"/stories/episodes/{episode['id']}/words", headers=headers, json={"term": "de kerk"}).status_code == 404
    manual = client.post("/words", headers=headers, json={"term": "de buurvrouw", "meaning_en": "the neighbour (f)"})
    assert manual.status_code == 201
    due = client.get("/words", headers=headers, params={"due": "true"}).json()
    assert due["due_count"] == 2 and due["total"] == 2 and due["new_count"] == 2
    item_id = saved["item"]["id"]
    reviewed = client.post(f"/words/{item_id}/review", headers=headers, json={"request_id": "rev-1", "grade": "good"}).json()
    assert reviewed["interval_days"] == 1 and reviewed["due"] is False
    client.post(f"/words/{item_id}/review", headers=headers, json={"request_id": "rev-1", "grade": "good"})
    with session_scope() as session:
        item = session.get(VocabItem, uuid.UUID(item_id))
        assert item.repetitions == 1, "a retried review is not scheduled twice"
    plan = client.get("/today", headers=headers).json()
    assert plan["words"] == {"due_count": 1, "total": 2, "learned_count": 0, "new_count": 1,
                             "preview": plan["words"]["preview"]}
    assert plan["goal"]["points"] == 1
    lapsed = client.post(f"/words/{item_id}/review", headers=headers, json={"request_id": "rev-2", "grade": "again"}).json()
    assert lapsed["lapses"] == 1 and lapsed["interval_days"] == 0
    assert client.delete(f"/words/{manual.json()['item']['id']}", headers=headers).status_code == 204
    assert client.get("/words", headers=headers).json()["total"] == 1
    with session_scope() as session:
        export_view = service.export(session, _learner(session).id)
    assert export_view["series"]["title"] == "De Lindestraat" and len(export_view["episodes"]) == 1


def test_translation_is_cached_after_one_model_call(client, headers):
    episode = ready_episode(client, headers)
    first = client.post(f"/stories/episodes/{episode['id']}/translate", headers=headers,
                        json={"request_id": "tr-1", "paragraph_index": 1}).json()
    assert first["fa"] and first["cached"] is False
    second = client.post(f"/stories/episodes/{episode['id']}/translate", headers=headers,
                         json={"request_id": "tr-2", "paragraph_index": 1}).json()
    assert second == {**first, "cached": True}
    chat = get_providers().chat
    assert sum(1 for call in chat.calls if call["prompt_version"] == "story-translate-v1") == 1
    assert client.get(f"/stories/episodes/{episode['id']}", headers=headers).json()["paragraphs"][1]["fa"] == first["fa"]


def test_read_aloud_compares_words_without_inventing_a_score(client, headers):
    episode = ready_episode(client, headers)
    from dlp.main import app

    spoken = FixtureSpeechToText(default_text="Sami lacht. Hij koopt een koekje voor Baas. Baas laat de sleutel los. "
                                              "Dank je wel Baas, zegt Sami. Nu kan hij naar de fietsenwinkel.")
    app.dependency_overrides[providers_dep] = lambda: replace(get_providers(), stt=spoken)
    try:
        wav = (FIXTURES / "tone_1s.wav").read_bytes()
        response = client.post(f"/stories/episodes/{episode['id']}/read-aloud", headers=headers,
                               data={"paragraph_index": "3"}, files={"audio": ("take.wav", wav, "audio/wav")})
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["matched_words"] == 25 and body["target_words"] == 35 and body["points"] == 5 and "score" not in body
    assert "postbode" in body["missed"] and body["extra"] == []
    stored = client.get(f"/stories/episodes/{episode['id']}", headers=headers).json()["read_aloud"]
    assert stored["3"]["attempts"] == 1 and stored["3"]["matched_words"] == 25


def test_default_level_skips_the_absolute_beginner_bridge(database):
    with session_scope() as session:
        learner = Learner(subject="fixture:level@example.com", email="level@example.com")
        session.add(learner)
        session.flush()
        assert service.default_stage(session, learner.id) == "a1"


def test_theme_rotation_avoids_recent_topics():
    first_id, first_title = service.pick_theme("a1", 1, set())
    second_id, _ = service.pick_theme("a1", 2, {first_id})
    assert first_id != second_id and first_title
    assert service.pick_theme("a1", 1, set()) == (first_id, first_title), "deterministic per episode number"


@pytest.mark.parametrize("stage", ["pre-a1", "b1", "c2"])
def test_stage_vocabulary_is_cumulative(stage):
    words = service.stage_vocabulary(stage)
    assert len(words) >= 500 and "toonbank" not in words[:0]
    assert Path(__file__).exists()
