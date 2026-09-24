"""Topic counts, task validity, skill-specific evidence, privacy and existing provider boundaries."""
from __future__ import annotations

import io
import json
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import func, select

from dlp.db.session import session_scope
from dlp.domains.curriculum import service, topics
from dlp.domains.curriculum.library import library_for
from dlp.domains.curriculum.models import CurriculumPractice, TopicPractice
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS
from dlp.domains.identity.models import Learner

from .conftest import auth_headers
from .test_curriculum import answers, install_assessor, new_recording


def loc(value):
    return {"nl": value, "en": f"English {value}", "fa": f"فارسی {value}"}


@pytest.fixture
def bank_data():
    words = library_for("pre-a1").vocabulary
    items = []
    for index in range(100):
        key = f"pre-a1-t{index + 1:03d}"
        def activity(skill, index=index, key=key):
            return {"text": loc(f"{'Brief' if skill == 'reading' else 'Voicemail'} {index}: Sam komt om tien uur."),
                    "questions": [{"id": f"{key}-{skill}-{q}", "prompt": loc(f"Welke tijd? Vraag {q}"),
                                   "options": [loc("Tien uur"), loc("Elf uur")], "answer_index": 0,
                                   "explanation": loc("Sam zegt: tien uur.")} for q in range(2)]}
        def task(skill, index=index):
            return {"prompt": loc(f"{'Zeg' if skill == 'speaking' else 'Schrijf'} uw antwoord voor afspraak {index}."),
                    "criteria": [loc("Geef uw naam.")], "sample": loc("Ik ben Sam."),
                    "min_words": 2, "max_words": 20, "sample_is_excerpt": False}
        items.append({"id": key, "title": loc(f"Afspraak {index}"), "category": loc("Werk" if index < 50 else "Thuis"),
                      "objectives": [loc("Bevestig de afspraak.")], "language_focus": loc("Naam en tijd"),
                      "vocabulary_ids": [words[index].id], "reading": activity("reading"),
                      "listening": activity("listening"), "speaking": task("speaking"), "writing": task("writing")})
    return {"schema_version": 1, "stage_id": "pre-a1", "review_status": "unreviewed", "topics": items}


@pytest.fixture
def bank(bank_data, monkeypatch):
    bank = topics.TopicBank.model_validate(bank_data)
    real = topics.topics_for
    monkeypatch.setattr(topics, "topics_for", lambda stage: bank if stage == bank.stage_id else real(stage))
    return bank


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_published_bank_has_at_least_100_distinct_topics_for_each_skill(stage_id):
    bank = topics.topics_for(stage_id)
    assert len(bank.topics) >= 100
    assert bank.review_status == "unreviewed"
    for skill in SKILLS:
        assert len([getattr(topic, skill) for topic in bank.topics]) >= 100
    for skill in ("reading", "listening"):
        positions = {q.answer_index for topic in bank.topics for q in getattr(topic, skill).questions}
        assert len(positions) > 1, (stage_id, skill, "correct answers must vary position")


@pytest.mark.parametrize("case", ["few-topics", "same-title", "same-reading", "same-listening", "same-speaking",
                                  "same-writing", "same-source", "bad-question", "duplicate-question", "repeated-option",
                                  "blank-translation", "wrong-stage", "bad-sample", "long-speaking", "false-excerpt",
                                  "duplicate-vocabulary", "invented-review"])
def test_bank_cannot_pad_counts_or_misrepresent_content(bank_data, case):
    first, second = bank_data["topics"][:2]
    if case == "few-topics":
        bank_data["topics"].pop()
    elif case == "same-title":
        second["title"] = loc("  AFSPRAAK 0 ")
    elif case.startswith("same-") and case.split("-")[1] in SKILLS:
        skill = case.split("-")[1]
        field = "text" if skill in ("reading", "listening") else "prompt"
        second[skill][field] = deepcopy(first[skill][field])
    elif case == "same-source":
        first["listening"]["text"] = deepcopy(first["reading"]["text"])
    elif case == "bad-question":
        first["reading"]["questions"][0]["answer_index"] = 5
    elif case == "duplicate-question":
        first["listening"]["questions"][0]["id"] = first["reading"]["questions"][0]["id"]
    elif case == "repeated-option":
        first["reading"]["questions"][0]["options"][1] = loc("  TIEN uur ")
    elif case == "blank-translation":
        first["writing"]["criteria"][0]["fa"] = " "
    elif case == "wrong-stage":
        bank_data["stage_id"] = "c2"
    elif case == "bad-sample":
        first["writing"]["sample"]["nl"] = "Ik"
    elif case == "long-speaking":
        first["speaking"]["max_words"] = 101
    elif case == "false-excerpt":
        first["speaking"]["sample_is_excerpt"] = True
    elif case == "duplicate-vocabulary":
        first["vocabulary_ids"] *= 2
    elif case == "invented-review":
        bank_data["review_status"] = "approved"
    with pytest.raises(ValidationError):
        topics.TopicBank.model_validate(bank_data)


def test_question_ids_bound_to_topic_prevent_cross_topic_replay(bank_data):
    bank_data["topics"][1]["reading"]["questions"][0]["id"] = "pre-a1-t001-unrelated"
    with pytest.raises(ValidationError, match="own topic"):
        topics.TopicBank.model_validate(bank_data)


def test_bank_references_and_filename_are_bound_to_stage(bank_data, tmp_path, monkeypatch):
    directory = tmp_path / "practice"
    directory.mkdir()
    monkeypatch.setattr(topics, "CONTENT_DIR", tmp_path)
    (directory / "a1.json").write_text(json.dumps(bank_data))
    with pytest.raises(ValueError, match="requested stage"):
        topics.topics_for("a1")
    bank_data["topics"][0]["vocabulary_ids"] = ["c2-other-word"]
    (directory / "pre-a1.json").write_text(json.dumps(bank_data))
    with pytest.raises(ValueError, match="outside this stage"):
        topics.topics_for("pre-a1")
    for bad in ("../secrets", "a3", "A1", "../a1"):
        with pytest.raises(service.CurriculumError) as error:
            topics.topics_for(bad)
        assert error.value.status_code == 404


def test_topic_api_auth_bounds_and_read_only_browsing(client, headers, bank):
    base = "/curriculum/pre-a1/topics"
    for path in (base, f"{base}/{bank.topics[0].id}"):
        assert client.get(path, params={"skill": "reading"}).status_code == 401
        assert client.get(path, headers=headers).status_code == 422
    for params in ({"skill": "grammar"}, {"skill": "reading", "limit": 25}, {"skill": "reading", "offset": -1},
                   {"skill": "reading", "status": "passed"}, {"skill": "reading", "q": "x" * 121}):
        assert client.get(base, params=params, headers=headers).status_code == 422
    listing = client.get(base, params={"skill": "reading"}, headers=headers).json()
    assert listing["total"] == listing["total_topics"] == 100 and len(listing["items"]) == 12
    assert listing["completed_count"] == 0 and not any(item["attempted"] for item in listing["items"])
    next_page = client.get(base, params={"skill": "reading", "offset": 12}, headers=headers).json()
    assert not {x["id"] for x in listing["items"]} & {x["id"] for x in next_page["items"]}
    search = client.get(base, params={"skill": "reading", "category": "Thuis", "q": "فارسی Afspraak 99"},
                        headers=headers).json()
    assert search["total"] == 1
    detail = client.get(f"{base}/{bank.topics[0].id}", params={"skill": "listening"}, headers=headers)
    assert "answer_index" not in detail.text and "explanation" not in detail.text
    assert detail.json()["activity"]["audio_parts"] >= 1
    assert not detail.json()["progress"]["attempted"]
    productive = client.get(f"{base}/{bank.topics[0].id}", params={"skill": "writing"}, headers=headers)
    assert productive.json()["context"] == {"reading": bank.topics[0].reading.text.model_dump(),
                                             "listening": bank.topics[0].listening.text.model_dump()}
    assert "answer_index" not in productive.text and "explanation" not in productive.text
    assert client.get(f"{base}/a1-t001", params={"skill": "reading"}, headers=headers).status_code == 404
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
        assert session.scalar(select(func.count()).select_from(CurriculumPractice)) == 0


def submit_reading(client, headers, topic, *, skill="reading", correct=True):
    questions = getattr(topic, skill).questions
    response = answers(questions) if correct else {q.id: (q.answer_index + 1) % len(q.options) for q in questions}
    return client.post(f"/curriculum/pre-a1/topics/{topic.id}/practice", headers=headers,
                       json={"skill": skill, "answers": response})


def test_topic_results_survive_retry_and_never_mix_skills_topics_or_people(client, headers, bank):
    first, second = bank.topics[:2]
    rejected = client.post(f"/curriculum/pre-a1/topics/{second.id}/practice", headers=headers,
                           json={"skill": "reading", "answers": answers(first.reading.questions)})
    assert rejected.status_code == 422
    first_try = submit_reading(client, headers, first, correct=False)
    assert first_try.status_code == 200 and not first_try.json()["completed"]
    passed = submit_reading(client, headers, first).json()
    assert passed["passed"] and passed["completed"]
    assert all("answer_index" in item and item["correct"] for item in passed["explanations"])
    retry = submit_reading(client, headers, first, correct=False).json()
    assert not retry["passed"] and retry["completed"]
    reading = client.get("/curriculum/pre-a1/topics?skill=reading&status=completed", headers=headers).json()
    assert reading["total"] == reading["completed_count"] == 1 and reading["items"][0]["id"] == first.id
    not_started = client.get("/curriculum/pre-a1/topics?skill=reading&status=not_started", headers=headers).json()
    assert not_started["total"] == 99
    listening = client.get("/curriculum/pre-a1/topics?skill=listening", headers=headers).json()
    assert listening["completed_count"] == 0
    other = client.get("/curriculum/pre-a1/topics?skill=reading", headers=auth_headers(email="second@example.com")).json()
    assert other["completed_count"] == 0 and other["learner_key"] != reading["learner_key"]
    with session_scope() as session:
        rows = list(session.scalars(select(TopicPractice)))
        assert len(rows) == 1 and rows[0].completed and not rows[0].latest_passed
        assert rows[0].evidence["result"]["correct"] == 0
    progress = client.get("/curriculum/pre-a1", headers=headers).json()["progress"]
    assert progress["practice_completed"] == ["reading"] and not progress["test_available"]


def test_listening_audio_never_completes_practice_and_is_bounded(client, headers, bank):
    path = f"/curriculum/pre-a1/topics/{bank.topics[0].id}/listening"
    assert client.post(path).status_code == 401
    assert client.post(path, headers=headers).status_code == 200
    assert client.post(path + "?part=99", headers=headers).status_code == 404
    assert client.post(path + "?part=-1", headers=headers).status_code == 422
    assert not client.get("/curriculum/pre-a1", headers=headers).json()["progress"]["practice_completed"]
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0


def test_productive_topics_use_real_owned_recording_and_context_and_existing_allowance(client, headers, bank, monkeypatch):
    first = bank.topics[0]
    client.get("/curriculum", headers=headers)
    client.get("/curriculum", headers=auth_headers(email="second@example.com"))
    foreign = new_recording("Ik ben Sam.", email="second@example.com")
    path = f"/curriculum/pre-a1/topics/{first.id}/practice"
    calls = install_assessor(monkeypatch)
    assert client.post(path, headers=headers, json={"skill": "speaking", "text": "Ik ben Sam."}).status_code == 422
    assert client.post(path, headers=headers,
                       json={"skill": "speaking", "audio_asset_id": foreign}).status_code == 422
    own = new_recording("Ik ben Noor.")
    response = client.post(path, headers=headers,
                           json={"skill": "speaking", "audio_asset_id": own, "text": "forged ignored transcript"})
    assert response.status_code == 200, response.text
    assert response.json()["completed"] and response.json()["passed"]
    assert json.loads(calls[0][1].content)["learner_response"] == "Ik ben Noor."
    assert first.reading.text.nl in calls[0][0].content and first.listening.text.nl in calls[0][0].content
    assert len(calls) == 1
    with session_scope() as session:
        saved = session.scalar(select(TopicPractice))
        assert saved.skill == "speaking" and saved.evidence["audio_asset_id"] == own
        assert saved.evidence["text"] == "Ik ben Noor."
    assert client.get("/curriculum/pre-a1", headers=headers).json()["progress"]["practice_completed"] == ["speaking"]


def test_provider_outage_and_invalid_draft_never_complete_topic(client, headers, bank, monkeypatch):
    first = bank.topics[0]
    path = f"/curriculum/pre-a1/topics/{first.id}/practice"
    calls = install_assessor(monkeypatch, fail_on=1)
    assert client.post(path, headers=headers, json={"skill": "writing", "text": "Ik"}).status_code == 422
    assert not calls
    result = client.post(path, headers=headers, json={"skill": "writing", "text": "Ik ben Sam."})
    assert result.status_code == 503
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
    assert not client.get("/curriculum/pre-a1", headers=headers).json()["progress"]["practice_completed"]



def test_allowance_refuses_topic_assessment_before_call_or_completion(client, headers, bank, monkeypatch, settings):
    calls = install_assessor(monkeypatch)
    monkeypatch.setattr(settings, "usage_daily_model_calls", 0)
    result = client.post(f"/curriculum/pre-a1/topics/{bank.topics[0].id}/practice", headers=headers,
                         json={"skill": "writing", "text": "Ik ben Sam."})
    assert result.status_code == 429 and calls == []
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
    assert not client.get("/curriculum/pre-a1", headers=headers).json()["progress"]["practice_completed"]


def test_fixture_topic_assessment_labels_unreviewed_response_without_pass(client, headers, bank):
    response = client.post(f"/curriculum/pre-a1/topics/{bank.topics[0].id}/practice", headers=headers,
                           json={"skill": "writing", "text": "Ik ben Sam."})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["completed"] and not result["passed"]
    assert "not assessed" in result["feedback"]["en"]
    assert all(not item["met"] for item in result["criteria"])

def test_topics_feed_four_skill_readiness_without_awarding_final_pass(client, headers, bank, monkeypatch):
    first = bank.topics[0]
    for skill in ("reading", "listening"):
        assert submit_reading(client, headers, first, skill=skill).status_code == 200
    calls = install_assessor(monkeypatch, fail_writing=True)
    for skill in ("writing", "speaking"):
        body = {"skill": skill, "text": "Ik ben Sam."}
        if skill == "speaking":
            body["audio_asset_id"] = new_recording("Ik ben Sam.")
        response = client.post(f"/curriculum/pre-a1/topics/{first.id}/practice", headers=headers, json=body)
        assert response.status_code == 200, response.text
        assert response.json()["completed"]
    assert len(calls) == 2
    status = client.get("/curriculum/pre-a1", headers=headers).json()["progress"]
    assert status["test_available"] and not status["passed"] and set(status["practice_completed"]) == set(SKILLS)
    assert client.post("/curriculum/pre-a1/test", headers=headers, json={"request_id": uuid.uuid4().hex}).status_code == 200


def test_topic_evidence_export_and_learner_deletion_are_private(client, headers, bank):
    assert submit_reading(client, headers, bank.topics[0]).status_code == 200
    mine = client.get("/export", headers=headers).json()["curriculum"]["topics"]
    assert len(mine) == 1 and mine[0]["topic_id"] == bank.topics[0].id
    assert mine[0]["evidence"]["answers"] == answers(bank.topics[0].reading.questions)
    assert "answer_index" not in json.dumps(mine)  # Saved evidence excludes the guided correction key.
    other = client.get("/export", headers=auth_headers(email="second@example.com")).json()
    assert other["curriculum"]["topics"] == []
    with session_scope() as session:
        owner = session.scalar(select(Learner).where(Learner.email == "owner@example.com"))
        session.delete(owner)
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
        assert session.scalar(select(func.count()).select_from(CurriculumPractice)) == 0


def test_topic_migration_is_additive_and_has_privacy_cascade():
    root = Path(__file__).resolve().parents[1]
    output = io.StringIO()
    config = Config(str(root / "alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "0003:0004", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE topic_practice" in sql
    assert "UNIQUE (learner_id, stage_id, topic_id, skill)" in sql
    assert "REFERENCES learners (id) ON DELETE CASCADE" in sql
    assert "DROP TABLE" not in sql


def test_release_refuses_invalid_topics_before_database_connection(monkeypatch):
    from dlp import release
    sequence = []
    monkeypatch.setattr(release, "curriculum", lambda: sequence.append("curriculum"))
    monkeypatch.setattr(release, "validate_all_libraries", lambda: sequence.append("libraries"))
    def invalid():
        sequence.append("topics")
        raise ValueError("topic coverage incomplete")
    monkeypatch.setattr(release, "validate_all_topics", invalid)
    monkeypatch.setattr(release, "create_engine", lambda *args, **kwargs: sequence.append("database"))
    with pytest.raises(ValueError, match="topic coverage"):
        release.migrate("postgresql+psycopg://dlp:dlp@localhost/dlp_test", "x" * 32)
    assert sequence == ["curriculum", "libraries", "topics"]
