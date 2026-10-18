"""Guided checks keep scores transient and never infer audio qualities from text."""
from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dlp.api.deps import context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.study import content, feedback
from dlp.domains.study.schemas import CoachReply, FeedbackBody
from dlp.domains.usage import service as usage
from dlp.providers.base import ChatResult, ProviderError
from dlp.providers.fixtures import FixtureChatModel

COPY = {"nl": "Gebruik hier ben bij ik.", "en": "Use ben with ik here."}


def lesson():
    return {"stage_id": "a1", "skill": "reading", "activity_id": "story-one",
            "parts": [{"id": "read", "prompt": COPY,
                       "text": [{"nl": "Sam fietst naar de school.", "en": "Sam cycles to school."}],
                       "questions": [
                           {"id": "q1", "kind": "choice", "prompt": COPY,
                            "options": [{"nl": "Fiets", "en": "Bike"}, {"nl": "Auto", "en": "Car"}],
                            "answer_index": 0, "explanation": COPY},
                           {"id": "q2", "kind": "short", "prompt": COPY,
                            "accepted_answers": ["school", "de school"], "explanation": COPY}],
                       "min_words": 1, "max_words": 100},
                      {"id": "retell", "prompt": COPY, "text": [], "questions": [],
                       "min_words": 1, "max_words": 100}]}


def test_objective_checks_use_own_keys_and_do_not_mix_language_into_comprehension():
    result = feedback.check_answers(lesson()["parts"][0], {"q1": 0, "q2": "De SCHOOL!"})
    assert result["score"] == 10
    assert result["dimensions"] == {"task": 10, "grammar": None, "vocabulary": None,
                                     "organisation": None, "pronunciation": None}
    assert result["ephemeral"] is True
    partial = feedback.check_answers(lesson()["parts"][0], {"q1": 0})
    assert partial["score"] == 5
    assert feedback.check_answers(lesson()["parts"][0], {"q1": True})["score"] == 0


def test_unknown_or_empty_objective_parts_cannot_award_a_score():
    with pytest.raises(CurriculumError):
        feedback.check_answers(lesson()["parts"][0], {"another-story-q": 0})
    with pytest.raises(CurriculumError):
        feedback.check_answers(lesson()["parts"][1], {})


def test_a_free_answer_paraphrase_outside_the_key_is_unassessed_rather_than_wrong():
    result = feedback.check_answers(lesson()["parts"][0], {"q1": 0, "q2": "Hij gaat naar school."})
    assert result["status"] == "needs_review"
    assert result["score"] is None and result["dimensions"]["task"] is None
    assert result["checks"][0]["correct"] is True
    assert result["checks"][1]["correct"] is None
    assert result["checks"][1]["review_required"] is True


def invoke(provider, *, text="Ik bent Sam.", skill="writing", answers=None):
    return feedback.evaluate(None, Settings(_env_file=None), provider,
                             learner_id=uuid.uuid4(), stage_id="a1", topic_id="family",
                             body=FeedbackBody(skill=skill, activity_id="story-one", part="retell", kind="response",
                                               text=text, answers=answers or {}), request_id="guided-request-0001")


def test_fixture_does_not_fabricate_scores_corrections_or_costs(monkeypatch):
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    provider = FixtureChatModel()
    result = invoke(provider)
    assert result["status"] == "fixture_unreviewed"
    assert result["score"] is None and all(value is None for value in result["dimensions"].values())
    assert result["corrected_text"] == "Ik bent Sam."
    assert result["corrections"] == [] and provider.calls == []


def stub_budget(monkeypatch):
    events = []
    monkeypatch.setattr(usage, "reserve", lambda session, settings, learner_id, metric, amount, request_id:
                        (events.append(("reserve", metric)) or SimpleNamespace(id=metric)))
    monkeypatch.setattr(usage, "started", lambda session, *ids: events.append(("start", ids)))
    monkeypatch.setattr(usage, "commit", lambda session, metric, amount: events.append(("commit", metric)))
    monkeypatch.setattr(usage, "release", lambda session, metric: events.append(("release", metric)))
    return events


def test_live_feedback_is_bounded_grounded_bilingual_and_pronunciation_is_not_inferred(monkeypatch):
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    events = stub_budget(monkeypatch)
    response = CoachReply(language_is_dutch=True,
                          dimensions={"task": 6, "grammar": 4, "vocabulary": 6, "organisation": 4},
                          summary=COPY, corrections=[{"original": "Ik bent", "replacement": "Ik ben",
                                                      "category": "grammar", "explanation": COPY}])
    class Model:
        name = "azure-strong"
        def complete_once(self, messages, **kwargs):
            assert kwargs["max_output_tokens"] == 1800
            assert kwargs["temperature"] == 0
            assert kwargs["schema"] is CoachReply
            assert json.loads(messages[1].content)["learner_text"] == "Ik bent Sam."
            assert "NEVER infer pronunciation" in messages[0].content
            return ChatResult("", response, "azure", "model", "v1", 100, 100, 1, 1)
    result = invoke(Model(), skill="speaking")
    assert result["score"] == 5
    assert result["corrected_text"] == "Ik ben Sam."
    assert result["dimensions"]["pronunciation"] is None
    assert result["ephemeral"] is True
    assert set(result["corrections"][0]["explanation"]) == {"nl", "en"}
    assert events == [("reserve", "model_calls"), ("reserve", "tokens"),
                      ("start", ("model_calls", "tokens")), ("commit", "model_calls"), ("commit", "tokens")]


def test_score_schema_rejects_out_of_range_or_invented_audio_dimensions():
    with pytest.raises(ValidationError):
        CoachReply(language_is_dutch=True, dimensions={"task": 11, "grammar": 5, "vocabulary": 5,
                                                     "organisation": 5}, summary=COPY)
    with pytest.raises(ValidationError):
        CoachReply(language_is_dutch=True, dimensions={"task": 5, "grammar": 5, "vocabulary": 5,
                                                     "organisation": 5, "pronunciation": 9}, summary=COPY)
    with pytest.raises(ValidationError):
        FeedbackBody(skill="writing", part="retell", kind="response", text="x", answers={"q": True})


def test_hallucinated_correction_is_refused_after_paid_usage_is_recorded(monkeypatch):
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    events = stub_budget(monkeypatch)
    class Model:
        name = "azure-strong"
        def complete_once(self, messages, **kwargs):
            reply = CoachReply(language_is_dutch=True,
                               dimensions={"task": 5, "grammar": 5, "vocabulary": 5, "organisation": 5},
                               summary=COPY, corrections=[{"original": "not in draft", "replacement": "new",
                                                          "category": "grammar", "explanation": COPY}])
            return ChatResult("", reply, "azure", "model", "v1", 100, 100, 1, 1)
    with pytest.raises(ProviderError):
        invoke(Model())
    assert events[-2:] == [("commit", "model_calls"), ("commit", "tokens")]


def test_explicit_semantic_review_uses_server_question_and_separates_language_from_comprehension(monkeypatch):
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    events = stub_budget(monkeypatch)
    class Model:
        name = "azure-strong"
        def complete_once(self, messages, **kwargs):
            payload = json.loads(messages[1].content)
            assert payload["task"] == COPY["nl"]
            assert payload["reference_answer"] == ["school", "de school"]
            assert payload["score_scope"] == "comprehension"
            reply = CoachReply(language_is_dutch=True,
                               dimensions={"task": 10, "grammar": 4, "vocabulary": 6, "organisation": 4},
                               summary=COPY, corrections=[])
            return ChatResult("", reply, "azure", "model", "v1", 100, 100, 1, 1)
    result = feedback.evaluate(None, Settings(_env_file=None), Model(),
                               learner_id=uuid.uuid4(), stage_id="a1", topic_id="family",
                               body=FeedbackBody(skill="listening", part="read", question_id="q2", kind="response",
                                                 text="Hij gaat naar school."), request_id="semantic-review-0001")
    assert result["score"] == 10  # understanding is not reduced by a lower grammar dimension
    assert result["score_kind"] == "semantic_comprehension"
    assert result["dimensions"]["grammar"] == 4
    assert result["dimensions"]["pronunciation"] is None
    assert events[-2:] == [("commit", "model_calls"), ("commit", "tokens")]


def test_route_feedback_no_store_and_no_learning_persistence(monkeypatch):
    from dlp.main import create_app

    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    app = create_app()
    ctx = SimpleNamespace(learner=SimpleNamespace(id=uuid.uuid4()), request_id="guided-ephemeral-0001")
    app.dependency_overrides[context_dep] = lambda: ctx
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[settings_dep] = lambda: Settings(_env_file=None)
    app.dependency_overrides[providers_dep] = lambda: SimpleNamespace(chat_strong=FixtureChatModel())
    # A None database makes an accidental attempt/progress write fail the
    # journey, rather than silently proving persistence using a mocked store.
    with TestClient(app) as client:
        response = client.post("/study/a1/topics/family/feedback", json={
            "skill": "reading", "activity_id": "story-one", "part": "read", "kind": "answers",
            "answers": {"q1": 0, "q2": "school"}})
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["score"] == 10
        assert response.json()["ephemeral"] is True


def test_ephemeral_transcription_retains_neither_audio_nor_transcript(monkeypatch):
    from pathlib import Path

    from dlp.domains.speech import service as speech
    from dlp.domains.speech.audio import AudioInfo
    from dlp.providers.fixtures import FixtureSpeechToText, MemoryBlobStore, tone_wav

    stub_budget(monkeypatch)
    info = AudioInfo(container="wav", codec="pcm_s16le", duration_seconds=1,
                     sample_rate=16000, channels=1, size_bytes=len(tone_wav(1)))
    def canonicalise(source, target, **kwargs):
        Path(target).write_bytes(tone_wav(1))
        return info
    monkeypatch.setattr(speech, "canonicalise", canonicalise)
    monkeypatch.setattr(speech, "_source_info", lambda *args: info)
    blob = MemoryBlobStore()
    # No Session object: any database write would fail this test. Even asking
    # to keep audio cannot override the explicitly transient mode.
    result = speech.transcribe_upload(None, Settings(_env_file=None), learner_id=uuid.uuid4(),
                                     request_id="ephemeral-speech-0001", upload_bytes=tone_wav(1),
                                     upload_filename="voice.wav", stt=FixtureSpeechToText(), blob=blob,
                                     keep_recording=True, persist_asset=False)
    assert result.transcript.text
    assert result.asset.id is None
    assert result.asset.meta["stored"] is False
    assert not blob.exists(result.asset.blob_key)


def test_selected_question_is_validated_before_provider_or_fixture_response(monkeypatch):
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: lesson())
    with pytest.raises(CurriculumError):
        feedback.evaluate(None, Settings(_env_file=None), FixtureChatModel(),
                          learner_id=uuid.uuid4(), stage_id="a1", topic_id="family",
                          body=FeedbackBody(skill="speaking", part="retell", question_id="other-part-question",
                                            kind="response", text="Ik ben Sam."), request_id="question-test-0001")


def test_guided_lesson_hides_answers_and_all_support_copy_is_bilingual(monkeypatch):
    from dlp.domains.study.schemas import IndexDocument, TopicDocument

    topics = TopicDocument.model_validate_json((content.CONTENT_DIR / "study/topics.json").read_text())
    pack = content.pack_for("pre-a1")
    source = pack.lessons[0]
    index = IndexDocument(schema_version=1, stages={"pre-a1": {
        skill: {source.topic_id: [{"source": "pack", "id": source.id}]}
        for skill in ("reading", "listening", "speaking", "writing")}})
    monkeypatch.setattr(content, "documents", lambda: (topics, index))
    # Real pack content, with a minimal vocabulary adapter, avoids a database
    # fixture and proves this read route never needs a progress record.
    monkeypatch.setattr(content, "topics_for", lambda stage: SimpleNamespace(topics=[]))
    monkeypatch.setattr(content, "library_for", lambda stage: SimpleNamespace(stories=[], vocabulary=[]))
    detail = content.lesson("pre-a1", source.topic_id, "reading", activity_id=source.id)
    serialized = json.dumps(detail)
    assert '"fa"' not in serialized
    assert '"answer_index"' not in serialized
    assert '"accepted_answers"' not in serialized
    assert len(detail["parts"][0]["text"]) >= 8
    assert detail["policy"]["ephemeral"] is True
    assert detail["preparation"]["grammar"]
    keys = content.lesson("pre-a1", source.topic_id, "reading", activity_id=source.id, include_answers=True)
    assert keys["parts"][0]["questions"][0]["answer_index"] >= 0
    # Public rendering must not mutate the authored answer key.
    assert source.questions[0].answer_index >= 0


def test_listening_sections_keep_the_authored_narrative_in_order():
    from dlp.domains.study.schemas import TopicDocument

    topics = TopicDocument.model_validate_json((content.CONTENT_DIR / "study/topics.json").read_text())
    source = content.pack_for("pre-a1").lessons[0]
    canonical = next(topic for topic in topics.topics if topic.id == source.topic_id)
    parts = content._pack_parts("pre-a1", canonical, source, "listening")
    assert [part["id"] for part in parts] == ["listen-gaps", "listen-choose", "listen-answer"]
    assert [line["nl"] for part in parts for line in part["text"]] == [line.nl for line in source.lines]
    assert all(part["questions"] for part in parts)
    assert [part["questions"][0]["kind"] for part in parts] == ["gap", "choice", "short"]


def test_authored_preparation_is_not_supplemented_with_inferred_rules(monkeypatch):
    document, _ = content.documents()
    source = next(item for item in content.pack_for("a2").lessons if item.topic_id == "family")
    canonical = next(item for item in document.topics if item.id == source.topic_id)
    monkeypatch.setattr(content, "library_for", lambda stage: SimpleNamespace(vocabulary=[]))

    def inferred_rules_must_not_run(*args):
        raise AssertionError("authored grammar must not be supplemented by automatic pattern guesses")

    monkeypatch.setattr(content, "_contextual_grammar", inferred_rules_must_not_run)
    preparation = content._pack_preparation("a2", canonical, source)
    assert preparation["grammar"] == [rule.model_dump() for rule in source.grammar]
    # Here voor marks a beneficiary, not a temporal relation. A literal token
    # match is insufficient to label this source sentence as a lesson in time.
    assert "Een moment met voor of na" not in {
        rule["title"]["nl"] for rule in preparation["grammar"]
    }


def test_authored_productive_and_listening_overrides_are_used_instead_of_generic_tasks():
    from dlp.domains.study.schemas import ListeningOverride, SpeakingOverride, TopicDocument, WritingOverride

    document = TopicDocument.model_validate_json((content.CONTENT_DIR / "study/topics.json").read_text())
    original = content.pack_for("pre-a1").lessons[0]
    canonical = next(topic for topic in document.topics if topic.id == original.topic_id)
    task = {"prompt": {"nl": "Schrijf een beknopte aanbeveling.", "en": "Write a concise recommendation."},
            "sample": {"nl": "Ik raad deze aanpak aan.", "en": "I recommend this approach."},
            "min_words": 4, "max_words": 80}
    sections = []
    for index, kind in enumerate(("gap", "choice", "short")):
        question = {"id": f"override-{index}", "kind": kind, "prompt": COPY, "explanation": COPY,
                    "options": [COPY, {"nl": "Andere keuze", "en": "Another choice"}] if kind == "choice" else [],
                    "answer_index": 1 if kind == "choice" else None,
                    "accepted_answers": [] if kind == "choice" else ["Gent", "in Gent"]}
        sections.append({"text": {"nl": f"Dit is deel {index}.", "en": f"This is section {index}."},
                         "questions": [question]})
    source = original.model_copy(update={
        "speaking": SpeakingOverride(short_questions=[task], description=task, discussion=task),
        "writing": WritingOverride(short=task, extended=task),
        "listening": ListeningOverride(sections=sections)})
    speaking = content._pack_parts("c1", canonical, source, "speaking")
    assert all(part["prompt"] == task["prompt"] for part in speaking)
    assert speaking[0]["practice_questions"][0]["id"] == "authored-1"
    assert speaking[2]["sample"] == task["sample"]
    writing = content._pack_parts("c1", canonical, source, "writing")
    assert all(part["prompt"] == task["prompt"] for part in writing)
    assert writing[1]["max_words"] == 80
    listening = content._pack_parts("c1", canonical, source, "listening")
    assert listening[2]["questions"][0]["accepted_answers"] == ["Gent", "in Gent"]
    assert listening[1]["text"][0]["nl"] == "Dit is deel 1."


def test_every_stage_and_skill_has_fifty_resolvable_topic_choices_without_answer_keys():
    from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS
    from dlp.domains.study.responses import StudyCatalogue, StudyLesson

    for stage_id in STAGE_IDS:
        for skill in SKILLS:
            catalogue = content.catalogue(stage_id, skill)
            StudyCatalogue.model_validate(catalogue)
            available = [topic for topic in catalogue["topics"] if topic["available"]]
            assert len(available) >= 50, (stage_id, skill, len(available))
            assert catalogue["available_topics"] == len(available)
            selected = available[0]
            detail = content.lesson(stage_id, selected["id"], skill)
            StudyLesson.model_validate({**detail, "policy": {**detail["policy"], "recording_max_seconds": 60}})
            assert detail["review_status"] == "unreviewed"
            assert detail["preparation"]["words"]
            assert detail["context"]["text"]
            assert detail["policy"]["ephemeral"] is True
            if skill == "reading":
                assert 8 <= len(detail["parts"][0]["text"]) <= 12
            for part in detail["parts"]:
                for question in part["questions"]:
                    assert "answer_index" not in question
                    assert "accepted_answers" not in question


def test_explicit_source_lesson_choices_keep_their_own_topic_context_and_foundation_prompts():
    from dlp.domains.study.responses import StudyLesson

    document, index = content.documents()
    checked = 0
    for stage, skills in index.stages.items():
        for skill, mappings in skills.items():
            for topic_id, references in mappings.items():
                for reference in references:
                    if reference.source != "practice" or "-t-source-" not in reference.id:
                        continue
                    checked += 1
                    detail = content.lesson(stage, topic_id, skill, activity_id=reference.id)
                    StudyLesson.model_validate({**detail, "policy": {**detail["policy"], "recording_max_seconds": 60}})
                    assert detail["activity_id"] == reference.id
                    assert detail["preparation"]["words"]
                    assert '"fa"' not in json.dumps(detail)
                    if stage == "pre-a1" and skill == "speaking":
                        path = content.CONTENT_DIR / "source-lessons" / f"{stage}.json"
                        source = next(item for item in json.loads(path.read_text())["topics"] if item["id"] == reference.id)
                        assert detail["parts"][-1]["prompt"] == content.bilingual(source["speaking"]["criteria"][-1])
                        assert detail["parts"][-1]["sample"] == content.bilingual(source["speaking"]["sample"])
    assert checked == 36  # twelve explicit source lessons, available in three productive/listening routes


def test_source_listening_uses_ordered_nonoverlapping_sections_and_grounded_answer_keys():
    from dlp.domains.study.schemas import SourceListeningDocument

    path = content.CONTENT_DIR / "study/source-listening.json"
    authored = SourceListeningDocument.model_validate_json(path.read_text())
    _, index = content.documents()
    indexed = {(stage, topic_id, source.id)
               for stage, skills in index.stages.items()
               for topic_id, references in skills["listening"].items()
               for source in references if source.source == "practice"}
    assert {(item.stage_id, item.activity_id) for item in authored.lessons} == {
        (stage, activity_id) for stage, _, activity_id in indexed}
    assert len(indexed) == 12
    for stage, topic_id, activity_id in indexed:
        original = next(item for item in json.loads((content.CONTENT_DIR / "source-lessons" / f"{stage}.json").read_text())[
            "topics"] if item["id"] == activity_id)["listening"]["text"]
        detail = content.lesson(stage, topic_id, "listening", activity_id=activity_id, include_answers=True)
        parts = detail["parts"]
        assert [part["id"] for part in parts] == ["listen-gaps", "listen-choose", "listen-answer"]
        for language in ("nl", "en"):
            assembled = " ".join(line[language] for part in parts for line in part["text"])
            assert " ".join(assembled.split()) == " ".join(original[language].split())
        for part, kind in zip(parts, ("gap", "choice", "short"), strict=True):
            script = " ".join(line["nl"] for line in part["text"])
            assert script and script != original["nl"]
            answers = {}
            for question in part["questions"]:
                assert question["kind"] == kind
                assert question["explanation"]["nl"] in script
                answer = question["answer_index"] if kind == "choice" else question["accepted_answers"][0]
                answers[question["id"]] = answer
                if kind == "gap":
                    assert answer.casefold() in script.casefold()
            assert feedback.check_answers(part, answers)["score"] == 10


def learning_row_counts():
    from sqlalchemy import text

    from dlp.db.session import session_scope

    tables = ("curriculum_attempts", "curriculum_practice", "topic_practice", "feedback_reports",
              "evidence_records", "practice_turns", "practice_sessions", "skill_records", "audio_assets",
              "jobs", "activity_events", "practice_observations", "exercise_items", "exercise_sessions",
              "learner_mistakes", "vocab_items", "story_episodes", "story_series", "word_suggestions",
              "learning_days", "coach_plan_requests")
    with session_scope() as session:
        return {table: session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() for table in tables}


def test_guided_objective_result_never_creates_learning_records(client, headers):
    catalogue = client.get("/study/pre-a1/topics", params={"skill": "reading"}, headers=headers)
    assert catalogue.status_code == 200
    topic = next(item for item in catalogue.json()["topics"] if item["available"])
    detail = content.lesson("pre-a1", topic["id"], "reading", include_answers=True)
    part = detail["parts"][0]
    before = learning_row_counts()
    response = client.post(f"/study/pre-a1/topics/{topic['id']}/feedback", headers=headers, json={
        "skill": "reading", "activity_id": detail["activity_id"], "part": part["id"], "kind": "answers",
        "answers": {question["id"]: question["answer_index"] for question in part["questions"]}})
    assert response.status_code == 200, response.text
    assert response.json()["score"] == 10
    assert response.headers["cache-control"] == "no-store"
    assert learning_row_counts() == before


def test_guided_recording_is_transcribed_without_saving_audio_or_transcript(client, headers):
    from dlp.providers.fixtures import tone_wav

    # Sign-in is a separate committed request before any paid-compatible work.
    assert client.get("/study/pre-a1/topics", params={"skill": "speaking"}, headers=headers).status_code == 200
    before = learning_row_counts()
    response = client.post("/study/pre-a1/topics/family/transcribe", headers=headers,
                           files={"audio": ("practice.wav", tone_wav(1), "audio/wav")})
    assert response.status_code == 200, response.text
    assert response.json()["transcript"]["text"]
    assert response.json()["audio"] == {"stored": False, "asset_id": None}
    assert response.json()["ephemeral"] is True
    assert learning_row_counts() == before
    counters = client.get("/usage", headers=headers).json()["counters"]
    assert counters["audio_seconds"]["daily"]["used"] == pytest.approx(1)
