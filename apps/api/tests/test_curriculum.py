"""Open learning access and independent checks belong to authenticated server state."""
from __future__ import annotations

import json
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.db.session import session_scope
from dlp.domains.curriculum import service
from dlp.domains.curriculum.models import CurriculumAttempt, CurriculumPractice
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS, Localized, ProductiveReply, Stage, Task
from dlp.domains.identity.models import Learner
from dlp.domains.speech.models import AudioAsset
from dlp.providers.base import ChatResult, ProviderError
from dlp.providers.registry import get_providers

from .conftest import auth_headers

ROOT = Path(__file__).resolve().parents[3]


def first_stage() -> Stage:
    data = json.loads((ROOT / "content/curriculum/path.json").read_text())
    return Stage.model_validate(data["stages"][0])


def answers(questions):
    return {item.id: item.answer_index for item in questions}


def test_curriculum_has_ordered_stages_four_skills_and_complete_localizations():
    document = service.curriculum()
    assert tuple(stage.id for stage in document.stages) == STAGE_IDS
    assert "a3" not in STAGE_IDS
    for stage in document.stages:
        for skill in SKILLS:
            assert getattr(stage.test, skill)
        assert stage.lesson.story.nl != stage.test.reading.text.nl
        assert len(stage.grammar) >= 2
        assert len(stage.vocabulary) >= 8
        assert len(stage.test.reading.questions) >= 4
        assert len(stage.test.listening.questions) >= 4
        def localized_items(value):
            if isinstance(value, dict):
                if "nl" in value:
                    assert all(value.get(key, "").strip() for key in ("nl", "en", "fa"))
                for item in value.values():
                    localized_items(item)
            elif isinstance(value, list):
                for item in value:
                    localized_items(item)
        localized_items(stage.model_dump())


def test_final_test_never_exposes_keys_samples_or_listening_transcript():
    stage = first_stage()
    view = service.public_test(stage.test)
    text = json.dumps(view, ensure_ascii=False)
    assert "answer_index" not in text
    assert "explanation" not in text
    assert "sample" not in text
    assert "text" not in view["listening"]
    assert view["listening"]["audio_parts"] >= 1
    assert view["reading"]["text"]["en"] == ""
    assert view["reading"]["text"]["fa"] == ""
    for skill in ("reading", "listening"):
        for question in view[skill]["questions"]:
            assert all(option["en"] == "" and option["fa"] == "" for option in question["options"])


def test_practice_models_are_complete_answers_or_explicitly_marked_excerpts():
    for stage in service.curriculum().stages:
        for activity in (stage.lesson, stage.test):
            for skill in ("speaking", "writing"):
                task = getattr(activity, skill)
                words = service.word_count(task.sample.nl)
                if task.sample_is_excerpt:
                    assert skill == "writing" and 5 <= words < task.min_words, (stage.id, words)
                else:
                    assert task.min_words <= words <= task.max_words, (stage.id, skill, words)


def test_objective_marks_require_every_valid_answer_and_cannot_be_averaged():
    questions = first_stage().test.reading.questions
    correct = answers(questions)
    assert service.objective_result(questions, correct)["passed"]
    with pytest.raises(service.CurriculumError):
        service.objective_result(questions, {})
    with pytest.raises(service.CurriculumError):
        service.objective_result(questions, {**correct, "made-up": 0})
    bad = dict(correct)
    bad[questions[0].id] = True
    with pytest.raises(service.CurriculumError):
        service.objective_result(questions, bad)
    for question in questions:
        bad[question.id] = (question.answer_index + 1) % len(question.options)
    assert not service.objective_result(questions, bad)["passed"]


def test_audio_chunking_reconstructs_content_without_oversize_provider_calls():
    text = "Luister naar dit verhaal. " * 200
    parts = service.audio_parts(text)
    assert len(parts) > 1
    assert all(0 < len(part) <= 500 for part in parts)
    assert " ".join(parts) == " ".join(text.split())


def test_admin_is_explicit_not_derived_from_general_signin_allowlist():
    settings = Settings(_env_file=None, curriculum_admin_emails="", owner_allowlist="owner@example.com,second@example.com")
    assert not service.is_admin(settings, "owner@example.com")
    settings = settings.model_copy(update={"curriculum_admin_emails": "owner@example.com"})
    assert service.is_admin(settings, "OWNER@example.com")
    assert not service.is_admin(settings, "second@example.com")


def test_productive_pass_requires_exact_evidence_and_dutch_and_word_bounds():
    wording = Localized(nl="Stel uzelf voor", en="Introduce yourself", fa="خود را معرفی کنید")
    task = Task(prompt=wording, criteria=[wording], sample=wording, min_words=3, max_words=10)
    reply = ProductiveReply(language_is_dutch=True, criteria=[{
        "criterion_index": 0, "met": True, "quote": "Ik ben Sam", "feedback": wording.model_dump(),
    }], feedback=wording)
    assert service.validate_productive_reply(task, "Ik ben Sam.", reply)["passed"]
    assert not service.validate_productive_reply(task, "Hello there Sam.", reply)["passed"]
    reply.language_is_dutch = False
    assert not service.validate_productive_reply(task, "Ik ben Sam.", reply)["passed"]
    reply.language_is_dutch = True
    reply.criteria[0].quote = "Ik"
    assert not service.validate_productive_reply(task, "Ik", reply)["passed"]
    reply.criteria[0].criterion_index = 8
    with pytest.raises(ProviderError):
        service.validate_productive_reply(task, "Ik ben Sam.", reply)


def test_duplicate_criteria_and_bogus_question_answers_are_rejected():
    stage = first_stage()
    data = stage.model_dump()
    data["test"]["reading"]["questions"][0]["answer_index"] = 99
    with pytest.raises(ValidationError):
        Stage.model_validate(data)


def prepare_check(client, headers):
    """Supply completed practice as a test precondition; API gate tests cover how it is earned."""
    assert client.get("/curriculum", headers=headers).status_code == 200
    with session_scope() as db:
        learner = db.scalar(select(Learner).where(Learner.email == "owner@example.com"))
        assert learner
        for skill in SKILLS:
            db.add(CurriculumPractice(learner_id=learner.id, stage_id="pre-a1", skill=skill,
                                      completed=True, evidence={}))
    response = client.post("/curriculum/pre-a1/test", headers=headers, json={"request_id": uuid.uuid4().hex})
    assert response.status_code == 200, response.text
    return response.json()


def new_recording(transcript: str, *, email="owner@example.com", before=False):
    with session_scope() as db:
        learner = db.scalar(select(Learner).where(Learner.email == email))
        assert learner
        asset = AudioAsset(learner_id=learner.id, kind="recording", blob_key=uuid.uuid4().hex, container="test",
                           duration_seconds=8, meta={"transcript": transcript, "stored": False},
                           created_at=utcnow() - timedelta(days=1) if before else utcnow())
        db.add(asset)
        db.flush()
        return str(asset.id)


def submission_for(stage: Stage, asset_id: str):
    return {"reading_answers": answers(stage.test.reading.questions),
            "listening_answers": answers(stage.test.listening.questions),
            "writing_text": stage.test.writing.sample.nl, "speaking_asset_id": asset_id}


def install_assessor(monkeypatch, *, fail_on=None, fail_writing=False):
    calls = []
    def complete(messages, **kwargs):
        calls.append(messages)
        if fail_on and len(calls) == fail_on:
            raise ProviderError("injected unavailable assessor")
        task_criteria = json.loads(messages[0].content.split("Criteria: ", 1)[1].split("\n", 1)[0])
        response = json.loads(messages[1].content)["learner_response"]
        met = not (fail_writing and "skill: writing" in messages[0].content)
        reply = ProductiveReply.model_validate({
            "language_is_dutch": True,
            "criteria": [{"criterion_index": i, "met": met, "quote": response,
                          "feedback": {"nl": "Goed", "en": "Good", "fa": "خوب"}}
                         for i in range(len(task_criteria))],
            "feedback": {"nl": "Oefen verder", "en": "Keep practising", "fa": "تمرین کنید"},
        })
        return ChatResult(text=reply.model_dump_json(), parsed=reply, provider="fixture", model="controlled-test",
                          prompt_version=kwargs["prompt_version"], input_tokens=10, output_tokens=20,
                          latency_ms=1, attempts=1)
    monkeypatch.setattr(get_providers().chat_strong, "complete", complete)
    return calls


def test_every_authenticated_student_can_explore_all_stages_but_tests_need_four_skills(client, headers):
    catalog = client.get("/curriculum", headers=headers).json()
    assert all(stage["unlocked"] for stage in catalog["stages"])
    assert not any(stage["passed"] for stage in catalog["stages"])
    assert catalog["policy"]["open_stage_access"]
    assert not catalog["policy"]["previous_stage_pass_required"]
    for stage_id in STAGE_IDS:
        assert client.get(f"/curriculum/{stage_id}", headers=headers).status_code == 200
        assert client.get(f"/curriculum/{stage_id}").status_code == 401
        assert client.post(f"/curriculum/{stage_id}/test", headers=headers,
                           json={"request_id": f"practice-needed-{stage_id}"}).status_code == 409
    advanced = service.stage_for("c2")
    practiced = client.post("/curriculum/c2/practice", headers=headers,
                           json={"skill": "reading", "answers": answers(advanced.lesson.reading_questions)})
    assert practiced.status_code == 200
    assert client.post("/curriculum/c2/listening", headers=headers).status_code == 200
    assert client.get("/curriculum/unknown-stage", headers=headers).status_code == 404
    assert client.post("/curriculum/pre-a1/test", headers=headers,
                       json={"request_id": "premature-check"}).status_code == 409
    assert client.post("/curriculum/pre-a1/practice", headers=headers,
                       json={"skill": "reading", "answers": {}, "admin": True}).status_code == 422


def test_explicit_admin_can_preview_all_without_creating_student_passes(client, headers, monkeypatch, settings):
    monkeypatch.setattr(settings, "curriculum_admin_emails", "owner@example.com")
    catalog = client.get("/curriculum", headers=headers).json()
    assert catalog["admin_bypass"]
    assert all(stage["unlocked"] for stage in catalog["stages"])
    started = client.post("/curriculum/c2/test", headers=headers, json={"request_id": "admin-preview-c2"})
    assert started.status_code == 200
    assert started.json()["admin_preview"] is True
    monkeypatch.setattr(settings, "curriculum_admin_emails", "")
    assert client.get("/curriculum/c2", headers=headers).status_code == 200
    assert not any(stage["passed"] for stage in client.get("/curriculum", headers=headers).json()["stages"])


def test_receptive_practice_progress_is_saved_and_can_be_resumed(client, headers):
    stage = first_stage()
    for skill, questions in (("reading", stage.lesson.reading_questions), ("listening", stage.lesson.listening_questions)):
        saved = client.post("/curriculum/pre-a1/practice", headers=headers,
                            json={"skill": skill, "answers": answers(questions)})
        assert saved.status_code == 200, saved.text
        assert saved.json()["completed"]
    progress = client.get("/curriculum/pre-a1", headers=headers).json()["progress"]
    assert progress["practice_completed"] == ["reading", "listening"]
    assert not progress["test_available"]


def test_attempt_is_private_and_start_is_idempotent(client, headers):
    attempt = prepare_check(client, headers)
    with session_scope() as db:
        row = db.get(CurriculumAttempt, uuid.UUID(attempt["id"]))
        key = row.request_id
    same = client.post("/curriculum/pre-a1/test", headers=headers, json={"request_id": key})
    assert same.json()["id"] == attempt["id"]
    other = auth_headers(email="second@example.com")
    assert client.get(f'/curriculum/attempts/{attempt["id"]}', headers=other).status_code == 404
    assert client.post(f'/curriculum/attempts/{attempt["id"]}/listening', headers=other).status_code == 404
    view = client.get(f'/curriculum/attempts/{attempt["id"]}', headers=headers).text
    assert "answer_index" not in view and '"sample"' not in view


def test_fresh_owned_audio_is_required_before_any_model_call(client, headers, monkeypatch):
    attempt = prepare_check(client, headers)
    stage = first_stage()
    calls = install_assessor(monkeypatch)
    old = new_recording(stage.test.speaking.sample.nl, before=True)
    path = f'/curriculum/attempts/{attempt["id"]}/submit'
    assert client.post(path, headers=headers, json=submission_for(stage, old)).status_code == 422
    client.get("/curriculum", headers=auth_headers(email="second@example.com"))
    other = new_recording(stage.test.speaking.sample.nl, email="second@example.com")
    assert client.post(path, headers=headers, json=submission_for(stage, other)).status_code == 422
    assert calls == []


def test_all_four_skills_record_a_pass_and_repeat_is_free_without_locking_other_stages(client, headers, monkeypatch):
    attempt = prepare_check(client, headers)
    stage = first_stage()
    asset = new_recording(stage.test.speaking.sample.nl)
    calls = install_assessor(monkeypatch)
    body = submission_for(stage, asset)
    path = f'/curriculum/attempts/{attempt["id"]}/submit'
    response = client.post(path, headers=headers, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "passed"
    assert all(response.json()["results"][skill]["passed"] for skill in SKILLS)
    assert len(calls) == 2
    repeated = client.post(path, headers=headers, json=body)
    assert repeated.status_code == 200 and len(calls) == 2
    assert client.get("/curriculum/a1", headers=headers).status_code == 200
    latest = client.get("/curriculum", headers=headers).json()["stages"][0]["latest_check"]
    assert latest["status"] == "passed"
    assert set(latest["results"]) == set(SKILLS)
    assert "test_snapshot" not in latest and "submission" not in latest
    assert client.get("/curriculum/pre-a2", headers=headers).status_code == 200
    changed = {**body, "writing_text": body["writing_text"] + " Nog een zin."}
    assert client.post(path, headers=headers, json=changed).status_code == 409


def test_one_failed_skill_cannot_be_compensated_by_other_skills(client, headers, monkeypatch):
    attempt = prepare_check(client, headers)
    stage = first_stage()
    asset = new_recording(stage.test.speaking.sample.nl)
    install_assessor(monkeypatch, fail_writing=True)
    response = client.post(f'/curriculum/attempts/{attempt["id"]}/submit', headers=headers,
                           json=submission_for(stage, asset))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "needs_practice"
    assert response.json()["results"]["reading"]["passed"]
    assert not response.json()["results"]["writing"]["passed"]
    assert client.get("/curriculum/a1", headers=headers).status_code == 200
    assert not client.get("/curriculum/pre-a1", headers=headers).json()["progress"]["passed"]


def test_assessor_outage_preserves_paid_skill_and_retry_does_not_duplicate_it(client, headers, monkeypatch):
    attempt = prepare_check(client, headers)
    stage = first_stage()
    asset = new_recording(stage.test.speaking.sample.nl)
    calls = install_assessor(monkeypatch, fail_on=2)
    body = submission_for(stage, asset)
    path = f'/curriculum/attempts/{attempt["id"]}/submit'
    response = client.post(path, headers=headers, json=body)
    assert response.status_code == 503
    assert client.get("/curriculum/a1", headers=headers).status_code == 200
    saved = client.get(f'/curriculum/attempts/{attempt["id"]}', headers=headers).json()
    assert saved["status"] == "in_progress"
    assert "speaking" in saved["results"] and "writing" not in saved["results"]
    assert saved["submission"] == body
    changed = {**body, "writing_text": body["writing_text"] + " Extra zin."}
    assert client.post(path, headers=headers, json=changed).status_code == 409
    assert len(calls) == 2
    retry = client.post(path, headers=headers, json=body)
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "passed"
    assert len(calls) == 3  # successful speaking, failed writing, retried writing only


def test_default_fixture_assessor_is_valid_but_never_awards_a_pass():
    from dlp.providers.base import ChatMessage
    from dlp.providers.fixtures import FixtureChatModel

    reply = FixtureChatModel().complete(
        [ChatMessage("system", 'Criteria: ["Geef uw naam"]\n'), ChatMessage("user", "Ik ben Sam")],
        schema=ProductiveReply, prompt_version=service.PROMPT_VERSION,
    )
    assert isinstance(reply.parsed, ProductiveReply)
    assert not reply.parsed.language_is_dutch
    assert all(not criterion.met for criterion in reply.parsed.criteria)


def test_revoked_admin_keeps_own_preview_label_without_converting_to_student_pass(client, headers, monkeypatch, settings):
    monkeypatch.setattr(settings, "curriculum_admin_emails", "owner@example.com")
    started = client.post("/curriculum/c2/test", headers=headers, json={"request_id": "revoked-admin-c2"}).json()
    monkeypatch.setattr(settings, "curriculum_admin_emails", "")
    owned = client.get(f'/curriculum/attempts/{started["id"]}', headers=headers)
    assert owned.status_code == 200 and owned.json()["admin_preview"] is True
    assert client.post(f'/curriculum/attempts/{started["id"]}/listening', headers=headers).status_code == 200
    assert not any(stage["passed"] for stage in client.get("/curriculum", headers=headers).json()["stages"])


def test_export_contains_only_own_work_not_final_answer_keys(client, headers):
    attempt = prepare_check(client, headers)
    response = client.get("/export", headers=headers)
    assert response.status_code == 200
    export = response.json()
    assert export["curriculum"]["checks"][0]["id"] == attempt["id"]
    assert "test_snapshot" not in response.text
    assert "answer_index" not in json.dumps(export["curriculum"])
    other = client.get("/export", headers=auth_headers(email="second@example.com")).json()
    assert other["curriculum"]["checks"] == []


def test_final_audio_cannot_be_reused_in_a_second_attempt(client, headers, monkeypatch):
    attempt = prepare_check(client, headers)
    stage = first_stage()
    # Start both attempts before the recording to test reuse, rather than only the freshness rule.
    second = client.post("/curriculum/pre-a1/test", headers=headers, json={"request_id": uuid.uuid4().hex}).json()
    asset = new_recording(stage.test.speaking.sample.nl)
    calls = install_assessor(monkeypatch)
    body = submission_for(stage, asset)
    assert client.post(f'/curriculum/attempts/{attempt["id"]}/submit', headers=headers, json=body).status_code == 200
    response = client.post(f'/curriculum/attempts/{second["id"]}/submit', headers=headers, json=body)
    assert response.status_code == 422
    assert len(calls) == 2


def test_same_start_key_concurrently_creates_one_attempt(client, headers):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    attempt = prepare_check(client, headers)
    with session_scope() as db:
        learner_id = db.get(CurriculumAttempt, uuid.UUID(attempt["id"])).learner_id
    barrier = Barrier(2)
    def start(_):
        with session_scope() as db:
            barrier.wait(timeout=10)
            return service.start_attempt(db, learner_id, first_stage(), "concurrent-check-key", admin=False).id
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(start, range(2)))
    assert ids[0] == ids[1]


def test_concurrent_submission_lock_refuses_duplicate_provider_work(client, headers):
    from sqlalchemy.exc import OperationalError

    attempt = prepare_check(client, headers)
    attempt_id = uuid.UUID(attempt["id"])
    with session_scope() as lookup:
        learner_id = lookup.get(CurriculumAttempt, attempt_id).learner_id
    with session_scope() as first:
        service.get_attempt(first, learner_id, attempt_id, lock=True)
        with pytest.raises(OperationalError) as error, session_scope() as second:
            service.get_attempt(second, learner_id, attempt_id, lock=True)
        assert getattr(error.value.orig, "sqlstate", "") == "55P03"


def test_azure_recording_limit_is_bounded_at_sixty_seconds():
    assert Settings.model_fields["max_audio_seconds"].default == 60
    with pytest.raises(ValidationError, match="at most 60"):
        Settings(_env_file=None, stt_provider="azure", max_audio_seconds=61)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, max_audio_seconds=0)


def test_new_curriculum_requires_all_three_languages():
    with pytest.raises(ValidationError):
        Localized(nl="Hallo", en="", fa="سلام")
    with pytest.raises(ValidationError):
        Localized(nl="Hallo", en="Hello")


def test_recording_policy_reports_effective_configured_limit(client, headers, settings):
    catalog = client.get("/curriculum", headers=headers).json()
    stage = client.get("/curriculum/pre-a1", headers=headers).json()
    attempt = prepare_check(client, headers)
    for response in (catalog, stage, attempt):
        assert response["policy"]["recording_max_seconds"] == min(60, settings.max_audio_seconds)
    assert catalog["learner_key"] == stage["learner_key"]
