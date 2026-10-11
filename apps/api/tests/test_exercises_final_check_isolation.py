"""The final check is never a source of practice (roadmap 3.8): no exercise module reads it, a lesson or topic
session is built and finished with the final check sealed off, and no final-check sentence or question id ends
up in any item, at any stage."""
from __future__ import annotations

import ast
import json
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.curriculum import service as curriculum
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.models import ExerciseItem
from tests.conftest import auth_headers

EXERCISES = Path(__file__).resolve().parents[1] / "src" / "dlp" / "domains" / "exercises"
# what only the final check is made of, or reads it
FORBIDDEN_ATTRIBUTES = {"test", "test_snapshot"}
FORBIDDEN_NAMES = {"Test", "ReceptiveTest", "public_test", "attempt_view", "start_attempt", "submit_attempt",
                   "CurriculumAttempt"}


class _Sealed:
    """Stands in for a stage's final check: any use of it fails the test."""

    def __getattr__(self, name):
        raise AssertionError(f"the final check was read ({name})")

    def __iter__(self):
        raise AssertionError("the final check was read")

    def __bool__(self):
        raise AssertionError("the final check was read")


def test_no_exercise_module_reads_the_final_check():
    for path in sorted(EXERCISES.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr not in FORBIDDEN_ATTRIBUTES, f"{path.name}:{node.lineno} reads .{node.attr}"
            elif isinstance(node, ast.Name):
                assert node.id not in FORBIDDEN_NAMES, f"{path.name}:{node.lineno} uses {node.id}"
            elif isinstance(node, ast.alias):
                assert node.name.rsplit(".", 1)[-1] not in FORBIDDEN_NAMES, f"{path.name} imports {node.name}"


def _sessions(client, stage_id: str, prefix: str) -> list[dict]:
    """A lesson session and a topic session for reading and for listening at one stage, run to the end."""
    views = []
    bodies = [{"source": "stage_skill", "stage_id": stage_id, "skill": skill} for skill in ("reading", "listening")]
    bodies += [{"source": "topic", "topic_id": f"{stage_id}-t001", "skill": skill} for skill in ("reading", "listening")]
    for index, body in enumerate(bodies):
        created = client.post("/exercises/sessions", headers=auth_headers(),
                              json={"request_id": f"{prefix}-{stage_id}-{index}", **body})
        assert created.status_code == 201, created.text
        view = created.json()
        for position, item in enumerate(view["items"]):
            action, payload = ("answer", {"answer": {"done": True}}) if item["kind"] != "choice" else (
                "skip", {"reason": "unknown"})
            answered = client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}",
                                   headers=auth_headers(),
                                   json={"request_id": f"{prefix}-{stage_id}-{index}-{position}", **payload})
            assert answered.status_code == 200, answered.text
        finished = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                               json={"request_id": f"{prefix}-{stage_id}-{index}-end", "early": True})
        assert finished.status_code == 200, finished.text
        views.append(view)
    return views


def test_lesson_and_topic_sessions_never_touch_the_final_check(client, monkeypatch):
    real = curriculum.curriculum()
    sealed = real.model_copy(update={"stages": [stage.model_copy(update={"test": _Sealed()})
                                                for stage in real.stages]})
    monkeypatch.setattr(curriculum, "curriculum", lambda: sealed)
    for stage_id in ("pre-a1", "b1", "c2"):
        _sessions(client, stage_id, "sealed")


def _sentences(text: str) -> list[str]:
    """The sentences of four words or more (a short name or a greeting may well appear elsewhere)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip().lower() for part in parts if len(part.split()) >= 4]


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_no_final_check_sentence_or_question_reaches_an_item(client, stage_id):
    stage = curriculum.stage_for(stage_id)
    views = _sessions(client, stage_id, "isolation")
    with session_scope() as session:
        rows = list(session.scalars(select(ExerciseItem).where(
            ExerciseItem.session_id.in_([uuid.UUID(view["id"]) for view in views]))))
    stored = json.dumps([[row.ref, row.prompt, row.key] for row in rows], ensure_ascii=False).lower()
    test = stage.test
    sentences = [sentence for part in (test.reading.text, test.listening.text, test.speaking.sample,
                                       test.writing.sample)
                 for sentence in _sentences(part.nl)]
    assert sentences
    for sentence in sentences:
        assert json.dumps(sentence, ensure_ascii=False)[1:-1] not in stored, sentence
    refs = {row.ref for row in rows}
    for question in [*test.reading.questions, *test.listening.questions]:
        assert f"question:{question.id}" not in refs and f"question:{stage_id}:{question.id}" not in refs
