"""Topic and lesson sessions (roadmap 3.8): the completion rules of the classic form, unchanged.

Only the first answers to a topic's or lesson's authored questions count, at finish, through objective_result
(75 %: both of a topic's two, all three of a lesson's); a miss put right on the second try does not; completion
stays once reached; a retry, a warm-up before an open task and a session finished with a question never tried
complete nothing. Evidence, observations and the export hold no answer key.
"""
from __future__ import annotations

import hashlib
import json
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from dlp.db.session import session_scope
from dlp.domains.coaching.models import PracticeObservation
from dlp.domains.curriculum import service as curriculum
from dlp.domains.curriculum import topics
from dlp.domains.curriculum.models import CurriculumPractice, TopicPractice
from dlp.domains.exercises import service
from dlp.domains.exercises.models import ExerciseItem, LearnerMistake
from dlp.domains.exercises.schemas import CreateBody
from tests.conftest import auth_headers

TOPIC = "a1-t001"


def _create(client, request_id, *, email="owner@example.com", **body):
    return client.post("/exercises/sessions", headers=auth_headers(email=email),
                       json={"request_id": request_id, **body})


def _topic(client, request_id, skill="reading", topic_id=TOPIC, **body):
    return _create(client, request_id, source="topic", topic_id=topic_id, skill=skill, **body)


def _lesson(client, request_id, skill="reading", stage_id="a1", **body):
    return _create(client, request_id, source="stage_skill", stage_id=stage_id, skill=skill, **body)


def _post(client, view, item, action, request_id, **body):
    return client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}",
                       headers=auth_headers(), json={"request_id": request_id, **body})


def _finish(client, view, request_id="finish-request-01", early=False):
    return client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                       json={"request_id": request_id, "early": early})


def _key(item) -> dict:
    with session_scope() as session:
        return session.scalar(select(ExerciseItem.key).where(ExerciseItem.id == uuid.UUID(item["id"])))


def _questions(view) -> list[dict]:
    return [item for item in view["items"] if item["kind"] == "choice"]


def _right(item) -> dict:
    return {"option": _key(item)["answer"]}


def _wrong(item) -> dict:
    answer = _key(item)["answer"]
    return {"option": next(option["id"] for option in item["prompt"]["options"] if option["id"] != answer)}


def _read(client, view, tag="x"):
    passage = view["items"][0]
    assert passage["kind"] in ("read_passage", "listen_passage")
    done = _post(client, view, passage, "answer", f"passage-{tag}-001", answer={"done": True})
    assert done.status_code == 200, done.text
    assert done.json()["outcome"] == "done" and done.json()["points"] == 0
    return done.json()


def _run(client, request_id, firsts, *, create=_topic, **body) -> dict:
    """Reads the passage, answers each question right (True) or wrong (False) the first time, puts a miss right
    on its second try, and finishes."""
    view = create(client, request_id, **body).json()
    _read(client, view, request_id)
    questions = _questions(view)
    for index, (item, right) in enumerate(zip(questions, firsts, strict=True)):
        answered = _post(client, view, item, "answer", f"{request_id}-q{index}a",
                         answer=_right(item) if right else _wrong(item))
        assert answered.status_code == 200, answered.text
        assert answered.json()["points"] == 1  # the first real answer earns the point, right or wrong
    for index, (item, right) in enumerate(zip(questions, firsts, strict=True)):
        if not right:
            again = _post(client, view, item, "answer", f"{request_id}-q{index}b", answer=_right(item))
            assert again.json()["outcome"] == "correct" and again.json()["attempt"] == 2
    finished = _finish(client, view, f"{request_id}-finish")
    assert finished.status_code == 200, finished.text
    return {"view": view, **finished.json()}


def _learner_id(email="owner@example.com"):
    from dlp.domains.identity.models import Learner
    with session_scope() as session:
        return session.scalar(select(Learner.id).where(Learner.email == email))


def _topic_row(topic_id=TOPIC, skill="reading"):
    with session_scope() as session:
        row = session.scalar(select(TopicPractice).where(TopicPractice.learner_id == _learner_id(),
                                                         TopicPractice.topic_id == topic_id,
                                                         TopicPractice.skill == skill))
        return None if row is None else {"completed": row.completed, "latest_passed": row.latest_passed,
                                         "content_version": row.content_version, "evidence": row.evidence}


def _stage_skill(stage_id="a1", skill="reading"):
    with session_scope() as session:
        return session.scalar(select(CurriculumPractice.completed).where(
            CurriculumPractice.learner_id == _learner_id(), CurriculumPractice.stage_id == stage_id,
            CurriculumPractice.skill == skill))


def _observations():
    with session_scope() as session:
        return [{"source": row.source, "request_id": row.request_id, "passed": row.passed,
                 "failed_refs": row.failed_refs, "summary": row.summary, "content_version": row.content_version,
                 "topic_id": row.topic_id, "skill": row.skill}
                for row in session.scalars(select(PracticeObservation).where(
                    PracticeObservation.learner_id == _learner_id()).order_by(PracticeObservation.created_at))]


def _topic_version(topic_id=TOPIC):
    topic = topics.topic_for(topics.topics_for(topic_id.rsplit("-t", 1)[0]), topic_id)
    return hashlib.sha256(topic.model_dump_json().encode()).hexdigest()


def test_a_topic_session_reads_first_and_asks_the_authored_questions_without_their_key(client):
    created = _topic(client, "topic-session-0001")
    assert created.status_code == 201, created.text
    view = created.json()
    assert (view["source"], view["topic_id"], view["skill"], view["retry"]) == ("topic", TOPIC, "reading", False)
    passage, *questions = view["items"]
    topic = topics.topic_for(topics.topics_for("a1"), TOPIC)
    # the passage in Dutch only, with the topic's own words; never graded
    assert passage["kind"] == "read_passage" and passage["skill"] == "reading"
    assert passage["prompt"]["text"] == {"nl": topic.reading.text.nl, "en": None, "fa": None}
    assert [word["term"] for word in passage["prompt"]["vocabulary"]]
    assert all(set(word["meaning"]) >= {"en", "fa"} for word in passage["prompt"]["vocabulary"])
    assert view["progress"] == {"closed": 0, "total": 2, "queued": 0}
    # the authored questions in their order, options shuffled under opaque ids, Dutch only, no key
    assert [_key(item)["question"] for item in questions] == [q.id for q in topic.reading.questions]
    for item, question in zip(questions, topic.reading.questions, strict=True):
        assert item["kind"] == "choice" and item["skill"] == "reading"
        assert item["prompt"]["direction"] == "question"
        assert sorted(option["nl"] for option in item["prompt"]["options"]) == sorted(o.nl for o in question.options)
        assert all(set(option) <= {"id", "nl", "en", "fa"} and not option.get("en")
                   for option in item["prompt"]["options"])
    text = json.dumps(view)
    assert "answer_index" not in text and "explanation" not in text and "positions" not in text
    for question in topic.reading.questions:
        assert question.explanation.nl not in text


def test_both_questions_right_first_time_complete_the_topic_and_the_stage_skill(client):
    finished = _run(client, "topic-session-0002", [True, True])
    completion = finished["summary"]["completion"]
    assert completion == {"scope": "topic", "skill": "reading", "topic_id": TOPIC, "counted": True, "reason": None,
                          "passed": True, "correct": 2, "total": 2, "required": 2, "completed": True,
                          "to_retry": 0}
    row = _topic_row()
    assert row["completed"] and row["latest_passed"] and row["content_version"] == _topic_version()
    assert _stage_skill() is True
    stage = client.get("/curriculum/a1", headers=auth_headers()).json()
    assert stage["progress"]["practice_completed"] == ["reading"]
    # one observation, as the classic form records one, under an id no client can send
    view = finished["view"]
    assert _observations() == [{"source": "topic_practice", "request_id": f"exercise:{view['id']}", "passed": True,
                                "failed_refs": [], "summary": {"correct": 2, "total": 2, "assessed": True},
                                "content_version": _topic_version(), "topic_id": TOPIC, "skill": "reading"}]
    # once every question is answered, the passage shows its translation
    again = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    text = again["items"][0]["prompt"]["text"]
    assert text["en"] and text["fa"]
    # a finish sent again says the same and records nothing twice
    replay = _finish(client, view, "topic-session-0002-finish").json()
    other = _finish(client, view, "another-finish-0001").json()
    assert replay["summary"] == other["summary"] == finished["summary"] and other["points"] == 0
    assert len(_observations()) == 1


def test_a_first_miss_does_not_complete_even_when_put_right(client):
    finished = _run(client, "topic-session-0003", [False, True])
    completion = finished["summary"]["completion"]
    assert completion["counted"] and not completion["passed"] and not completion["completed"]
    assert (completion["correct"], completion["required"], completion["to_retry"]) == (1, 2, 1)
    row = _topic_row()
    assert row["completed"] is False and row["latest_passed"] is False
    assert _stage_skill() is False
    topic = topics.topic_for(topics.topics_for("a1"), TOPIC)
    first = topic.reading.questions[0]
    [observation] = _observations()
    assert observation["passed"] is False and observation["failed_refs"] == [first.id]
    # the evidence keeps the answers given, the first one wrong, and no key
    assert row["evidence"]["answers"][first.id] != first.answer_index
    assert row["evidence"]["answers"][topic.reading.questions[1].id] == topic.reading.questions[1].answer_index
    assert "answer_index" not in json.dumps(row["evidence"])
    # the miss is a comprehension mistake on the question
    with session_scope() as session:
        mistake = session.scalar(select(LearnerMistake).where(LearnerMistake.learner_id == _learner_id()))
        assert (mistake.category, mistake.ref, mistake.skill) == ("comprehension", f"question:{first.id}", "reading")
    exported = client.get("/export", headers=auth_headers()).json()
    for section in ("curriculum", "exercises", "mistakes"):
        text = json.dumps(exported[section])
        assert "answer_index" not in text and "positions" not in text and first.explanation.nl not in text


def test_completion_stays_once_reached(client):
    assert _run(client, "topic-session-0004", [True, True])["summary"]["completion"]["completed"]
    later = _run(client, "topic-session-0005", [False, False])["summary"]["completion"]
    assert later["counted"] and not later["passed"] and later["completed"]
    row = _topic_row()
    assert row["completed"] is True and row["latest_passed"] is False
    assert [entry["passed"] for entry in _observations()] == [True, False]


def test_a_skipped_first_try_counts_as_wrong_and_a_question_never_tried_counts_for_nothing(client):
    view = _topic(client, "topic-session-0006").json()
    _read(client, view)
    first, second = _questions(view)
    skipped = _post(client, view, first, "skip", "skip-question-0001", reason="unknown")
    assert skipped.json()["outcome"] == "skipped" and skipped.json()["points"] == 0
    _post(client, view, second, "answer", "answer-question-0002", answer=_right(second))
    _post(client, view, first, "answer", "answer-question-0003", answer=_right(first))
    completion = _finish(client, view).json()["summary"]["completion"]
    assert completion["counted"] and not completion["passed"] and completion["correct"] == 1
    assert _topic_row()["evidence"]["skipped"] == [_key(first)["question"]]

    # finished early with a question never tried: no attempt was made, nothing is recorded
    view = _topic(client, "topic-session-0007", topic_id="a1-t002").json()
    _read(client, view, "early")
    first, _second = _questions(view)
    _post(client, view, first, "answer", "answer-question-0004", answer=_right(first))
    assert _finish(client, view, early=False).status_code == 409
    completion = _finish(client, view, "finish-early-0001", early=True).json()["summary"]["completion"]
    assert completion["counted"] is False and completion["reason"] == "unfinished"
    assert completion["completed"] is False and completion["to_retry"] == 1
    assert _topic_row("a1-t002") is None and len(_observations()) == 1


def test_a_retry_asks_only_the_missed_questions_and_completes_nothing(client):
    first_run = _run(client, "topic-session-0008", [False, True])
    missed = _key(_questions(first_run["view"])[0])["question"]
    created = _topic(client, "retry-session-0001", retry=True)
    assert created.status_code == 201, created.text
    view = created.json()
    assert view["retry"] is True and view["id"] != first_run["view"]["id"]
    assert [item["kind"] for item in view["items"]] == ["read_passage", "choice"]
    assert _key(_questions(view)[0])["question"] == missed
    _read(client, view, "retry")
    _post(client, view, _questions(view)[0], "answer", "retry-answer-0001", answer=_right(_questions(view)[0]))
    completion = _finish(client, view, "retry-finish-0001").json()["summary"]["completion"]
    assert completion["counted"] is False and completion["reason"] == "retry"
    assert completion["completed"] is False and completion["to_retry"] == 0
    assert _topic_row()["completed"] is False and len(_observations()) == 1
    # the last session on this topic missed nothing: there is nothing to retry
    nothing = _topic(client, "retry-session-0002", retry=True)
    assert nothing.status_code == 409 and nothing.json()["code"] == "nothing_to_retry"
    # nor on a topic never practised
    never = _topic(client, "retry-session-0003", topic_id="a1-t003", retry=True)
    assert never.status_code == 409 and never.json()["code"] == "nothing_to_retry"


def test_lesson_sessions_complete_the_stage_skill_without_an_observation(client):
    lesson = curriculum.stage_for("a1").lesson
    finished = _run(client, "lesson-session-0001", [True, True, True], create=_lesson)
    view = finished["view"]
    assert (view["source"], view["topic_id"], view["skill"]) == ("stage_skill", None, "reading")
    # lesson question ids repeat from stage to stage: the refs name the stage
    with session_scope() as session:
        refs = list(session.scalars(select(ExerciseItem.ref).where(ExerciseItem.session_id == uuid.UUID(view["id"]),
                                                                   ExerciseItem.kind == "choice")
                                    .order_by(ExerciseItem.position)))
    assert refs == [f"question:a1:{question.id}" for question in lesson.reading_questions]
    completion = finished["summary"]["completion"]
    assert completion["scope"] == "lesson" and completion["counted"] and completion["passed"]
    assert completion["total"] == completion["required"] == 3 and completion["completed"]
    assert _stage_skill() is True and _observations() == [] and _topic_row() is None

    # listening: heard part by part from the lesson's own route; the transcript only once answered
    view = _lesson(client, "lesson-session-0002", skill="listening").json()
    passage = view["items"][0]
    assert passage["kind"] == "listen_passage" and passage["prompt"]["parts"] == len(
        curriculum.audio_parts(lesson.listening.nl))
    assert passage["prompt"]["transcript"] is None and lesson.listening.nl not in json.dumps(view)
    _read(client, view, "listen")
    first, *rest = _questions(view)
    _post(client, view, first, "answer", "lesson-answer-0001", answer=_wrong(first))
    for index, item in enumerate(rest):
        _post(client, view, item, "answer", f"lesson-answer-1{index:03d}", answer=_right(item))
    assert client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()["items"][0][
        "prompt"]["transcript"] is None  # one question is still to be asked again
    _post(client, view, first, "answer", "lesson-answer-0002", answer=_right(first))
    revealed = client.get(f"/exercises/sessions/{view['id']}", headers=auth_headers()).json()
    assert revealed["items"][0]["prompt"]["transcript"]["nl"] == lesson.listening.nl
    completion = _finish(client, view, "lesson-finish-0002").json()["summary"]["completion"]
    assert completion["counted"] and not completion["passed"] and completion["completed"] is False
    assert _stage_skill(skill="listening") is False


def test_warm_ups_before_an_open_task_never_complete_and_typed_items_are_never_speaking(client):
    topic = topics.topic_for(topics.topics_for("a1"), TOPIC)
    for skill in ("speaking", "writing"):
        created = _topic(client, f"warm-up-session-{skill}", skill=skill)
        assert created.status_code == 201, created.text
        view = created.json()
        graded = [item for item in view["items"] if item["kind"] != "intro"]
        assert graded and all(item["kind"] not in ("read_passage", "listen_passage", "sentence_order")
                              for item in graded)
        for item in graded:
            # only the item said aloud is speaking; typing never is
            assert item["skill"] != "speaking" or item["kind"] == "shadow"
            assert item["skill"] != skill or item["kind"] == "shadow"
        # every item is about the topic's own words, boards too (an odd-one-out board's odd word excepted)
        with session_scope() as session:
            rows = list(session.scalars(select(ExerciseItem).where(ExerciseItem.session_id == uuid.UUID(view["id"]),
                                                                   ExerciseItem.kind != "intro")))
        assert _words(rows) and _words(rows) <= set(topic.vocabulary_ids)
        for index, item in enumerate(graded):
            skipped = _post(client, view, item, "skip", f"warm-up-skip-{skill}-{index:03d}", reason="unknown")
            assert skipped.status_code == 200, skipped.text
        # a skipped item is asked again at the end: the learner stops here
        completion = _finish(client, view, f"warm-up-finish-{skill}", early=True).json()["summary"]["completion"]
        assert completion == {"scope": "topic", "skill": skill, "topic_id": TOPIC, "counted": False,
                              "reason": "open_task", "passed": None, "correct": None, "total": None,
                              "required": None, "completed": False, "to_retry": 0}
    assert _topic_row(skill="speaking") is None and _topic_row(skill="writing") is None
    assert _stage_skill(skill="speaking") is None and _observations() == []


def _words(rows) -> set[str]:
    """The library words items are about: an item's own word, every word of a board (not odd one out's odd
    word, which comes from another topic by design)."""
    words: set[str] = set()
    for row in rows:
        refs = row.key.get("refs", {})
        if row.kind == "odd_one_out":
            words |= {ref for option, ref in refs.items() if option != row.key["answer"]}
        elif row.kind in ("match_pairs", "de_het"):
            words |= set(refs.values())
        else:
            words.add(row.ref)  # a choice's other options are distractors, not what it practises
    return {ref.split(":", 1)[1] for ref in words if ref.startswith(("word:", "sentence:"))}


def test_a_warm_up_keeps_to_the_topic_words_and_never_tags_typing_as_speaking():
    """Over many seeds, with the topic's words and the whole stage met (boards may then draw on known words):
    every item and board stays on the topic's words, typed kinds occur and are never speaking or writing, and
    only shadowing is speaking."""
    import random
    from typing import get_args

    from dlp.domains.exercises.blueprints import plan
    from dlp.domains.exercises.pool import pool_for
    from dlp.domains.exercises.schemas import GradedKind

    seen: set[str] = set()
    for stage_id, topic_id in (("a1", TOPIC), ("b1", "b1-t001"), ("c2", "c2-t001")):
        pool = pool_for(stage_id)
        topic = topics.topic_for(topics.topics_for(stage_id), topic_id)
        met = frozenset(word.key for word in pool.words)
        kinds = frozenset(get_args(GradedKind)) - {"sentence_order"}
        for seed in range(60):
            drafts = plan(pool, random.Random(seed), size=6, met=met, audio=seed % 2 == 0, kinds=kinds,
                          only=frozenset(topic.vocabulary_ids))
            graded = [draft for draft in drafts if draft.kind != "intro"]
            assert graded
            for draft in graded:
                seen.add(draft.kind)
                assert draft.skill in ("", "listening") or (draft.skill == "speaking" and draft.kind == "shadow")
                if draft.kind in ("match_pairs", "de_het"):
                    about = set(draft.words)
                elif draft.kind == "odd_one_out":
                    about = set(draft.words) - {draft.key["refs"][draft.key["answer"]].removeprefix("word:")}
                else:  # a choice's other options are distractors, not what it practises
                    about = {draft.ref.split(":", 1)[1]}  # word:<id>, or sentence:<id> for a built sentence
                assert about <= set(topic.vocabulary_ids), (stage_id, seed, draft.kind)
    assert {"typed_recall", "cloze_typed", "shadow"} <= seen


def test_a_session_on_changed_content_is_not_resumed(client, monkeypatch):
    """A session built before its topic changed could never count: a new request starts over."""
    first = _topic(client, "topic-session-0401").json()
    original = topics.topics_for
    real = original("a1")
    changed = [topic.model_copy(update={"language_focus": topic.objectives[0]}) if topic.id == TOPIC else topic
               for topic in real.topics]
    monkeypatch.setattr(topics, "topics_for",
                        lambda stage_id: real.model_copy(update={"topics": changed}) if stage_id == "a1"
                        else original(stage_id))
    again = _topic(client, "topic-session-0402")
    assert again.status_code == 201 and again.json()["id"] != first["id"] and not again.json()["resumed"]
    stale = client.get(f"/exercises/sessions/{first['id']}", headers=auth_headers()).json()
    assert stale["status"] == "abandoned"


def test_a_retry_left_open_is_not_resumed_once_a_newer_session_finished(client):
    first_run = _run(client, "topic-session-0501", [False, True])
    first_missed = _key(_questions(first_run["view"])[0])["question"]
    left_open = _topic(client, "retry-session-0501", retry=True).json()
    assert [_key(item)["question"] for item in _questions(left_open)] == [first_missed]
    second_run = _run(client, "topic-session-0502", [True, False])
    second_missed = _key(_questions(second_run["view"])[1])["question"]
    retry = _topic(client, "retry-session-0502", retry=True)
    assert retry.status_code == 201 and retry.json()["id"] != left_open["id"]
    assert [_key(item)["question"] for item in _questions(retry.json())] == [second_missed]
    # the same retry asked again resumes it
    again = _topic(client, "retry-session-0503", retry=True).json()
    assert again["resumed"] and again["id"] == retry.json()["id"]


def test_sessions_on_other_activities_never_resume_each_other(client):
    words = _create(client, "word-session-00001", stage_id="a1").json()
    lesson = _lesson(client, "lesson-session-0101").json()
    first = _topic(client, "topic-session-0101").json()
    other_topic = _topic(client, "topic-session-0102", topic_id="a1-t002").json()
    other_skill = _topic(client, "topic-session-0103", skill="listening").json()
    ids = [words["id"], lesson["id"], first["id"], other_topic["id"], other_skill["id"]]
    assert len(set(ids)) == 5 and not any(view["resumed"] for view in (lesson, first, other_topic, other_skill))
    again = _topic(client, "topic-session-0104")
    assert again.status_code == 200 and again.json()["resumed"] and again.json()["id"] == first["id"]
    # the word session is still open: a topic or lesson never takes its place
    resumed = _create(client, "word-session-00002", stage_id="a1").json()
    assert resumed["resumed"] and resumed["id"] == words["id"]


def test_a_topic_or_lesson_request_is_checked(client):
    bad = [
        {"source": "topic", "topic_id": TOPIC},  # no skill
        {"source": "topic", "skill": "reading"},  # no topic
        {"source": "stage_skill", "topic_id": TOPIC, "skill": "reading"},
        {"source": "stage_skill", "skill": "speaking"},  # a lesson session reads or listens
        {"source": "while_you_wait", "skill": "reading"},
        {"source": "topic", "topic_id": TOPIC, "skill": "reading", "size": 6},
        {"source": "topic", "topic_id": TOPIC, "skill": "writing", "retry": True},
        {"source": "topic", "topic_id": "../a1-t001", "skill": "reading"},
    ]
    for index, body in enumerate(bad):
        assert _create(client, f"bad-request-{index:04d}", **body).status_code == 422, body
    assert _topic(client, "missing-topic-0001", topic_id="a1-t999").status_code == 404
    assert _topic(client, "missing-topic-0002", stage_id="pre-a1").status_code == 404
    assert _lesson(client, "missing-stage-0001", stage_id="a3").status_code == 404
    with pytest.raises(ValidationError):
        CreateBody(request_id="body-request-01", source="topic", topic_id=TOPIC)
    # a word session's request is fingerprinted as before the topic fields existed
    params = service._params(CreateBody(request_id="body-request-02", stage_id="a1"))
    assert set(params) == {"source", "stage_id", "focus", "library_topic", "size", "fresh", "kinds"}


def test_content_changed_since_the_start_counts_for_nothing(client, monkeypatch):
    view = _topic(client, "topic-session-0201").json()
    _read(client, view, "changed")
    for index, item in enumerate(_questions(view)):
        _post(client, view, item, "answer", f"changed-answer-{index:04d}", answer=_right(item))
    original = topics.topics_for
    real = original("a1")
    changed = [topic.model_copy(update={"language_focus": topic.objectives[0]}) if topic.id == TOPIC else topic
               for topic in real.topics]
    monkeypatch.setattr(topics, "topics_for",
                        lambda stage_id: real.model_copy(update={"topics": changed}) if stage_id == "a1"
                        else original(stage_id))
    completion = _finish(client, view, "changed-finish-0001").json()["summary"]["completion"]
    assert completion["counted"] is False and completion["reason"] == "content_changed"
    assert _topic_row() is None and _observations() == []


def test_a_listening_passage_may_be_passed_when_sound_cannot_be_heard(client):
    view = _topic(client, "topic-session-0301", skill="listening").json()
    passage = view["items"][0]
    assert passage["kind"] == "listen_passage" and passage["prompt"]["parts"] >= 1
    skipped = _post(client, view, passage, "skip", "listen-skip-0001", reason="no_audio")
    assert skipped.status_code == 200 and skipped.json()["outcome"] == "done"
    # a reading passage has no sound to skip for
    reading = _topic(client, "topic-session-0302").json()
    assert _post(client, reading, reading["items"][0], "skip", "read-skip-0001",
                 reason="no_audio").status_code == 422
    assert _post(client, reading, reading["items"][0], "answer", "read-answer-0001",
                 answer={"option": "abcd"}).status_code == 422


def test_topic_sessions_need_no_word_pool(client, monkeypatch):
    """A stage whose library is too thin for word sessions still has its topics and lesson."""
    from dlp.domains.exercises import service as exercise_service

    def thin(stage_id):
        raise AssertionError("a reading or listening session builds no word pool")

    monkeypatch.setattr(exercise_service, "pool_for", thin)
    assert _topic(client, "no-pool-session-01").status_code == 201
    assert _lesson(client, "no-pool-session-02", skill="listening").status_code == 201
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0
