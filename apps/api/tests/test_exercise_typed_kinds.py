"""Typed, tile and sorting kinds (roadmap 3.4): what each grader says, which stage has which kind, and the
learner's own overrule, which never completes anything."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from dlp.db.session import session_scope
from dlp.domains.curriculum.models import TopicPractice
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.graders import InvalidAnswer, grade
from dlp.domains.exercises.models import ExerciseItem, LearnerMistake
from dlp.domains.exercises.pool import pool_for
from tests.conftest import auth_headers

# stage -> (words with a typed cloze, nouns to sort into de/het, words with a sentence to build, paragraphs to
#           put in order); the other kinds work for every word. Measured 10 Oct 2026 on the content of 6 Oct.
AVAILABLE = {
    "pre-a1": (448, 309, 194, 0),
    "a1": (448, 309, 259, 0),
    "pre-a2": (450, 309, 271, 0),
    "a2": (462, 320, 414, 0),
    "pre-b1": (459, 340, 289, 99),
    "b1": (457, 340, 217, 0),
    "pre-b2": (437, 400, 310, 100),
    "b2": (432, 400, 311, 200),
    "pre-c1": (416, 400, 315, 200),
    "c1": (488, 0, 283, 198),
    "pre-c2": (492, 0, 271, 199),
    "c2": (492, 0, 274, 199),
}


def test_which_stage_has_which_kind():
    assert list(AVAILABLE) == list(STAGE_IDS)
    for stage_id, row in AVAILABLE.items():
        available = pool_for(stage_id).available()
        measured = (available["cloze_typed"], available["de_het"], available["sentence_builder"],
                    available["sentence_order"])
        assert measured == row, f"{stage_id}: content changed; re-measure and update AVAILABLE on purpose"


RECALL = ({"kind": "typed_recall"}, {"accepted": ["het huis"], "article": "optional"})


@pytest.mark.parametrize(("text", "outcome", "notes"), [
    ("het huis", "correct", []),
    ("Huis", "correct", ["article_missing"]),
    ("het hius", "almost", ["spelling"]),
    ("de huis", "almost", ["article"]),
    ("de boom", "incorrect", ["article"]),
])
def test_typed_answers_are_judged_tolerantly(text, outcome, notes):
    judged = grade("typed_recall", *RECALL, {"text": text}, frozenset({"de boom"}))
    assert (judged.outcome, judged.feedback["notes"]) == (outcome, notes)
    assert judged.misses == (["answer"] if outcome == "incorrect" else []), "almost is never a mistake"


def test_a_board_is_judged_part_by_part():
    prompt = {"left": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
              "right": [{"id": "w"}, {"id": "x"}, {"id": "y"}, {"id": "z"}]}
    key = {"pairs": {"a": "w", "b": "x", "c": "y", "d": "z"}}
    assert grade("match_pairs", prompt, key, {"pairs": key["pairs"]}).outcome == "correct"
    swapped = grade("match_pairs", prompt, key, {"pairs": {"a": "x", "b": "w", "c": "y", "d": "z"}})
    assert swapped.outcome == "incorrect" and sorted(swapped.misses) == ["a", "b"]
    with pytest.raises(InvalidAnswer):
        grade("match_pairs", prompt, key, {"pairs": {"a": "w", "b": "w", "c": "y", "d": "z"}})
    sort = {"options": [{"id": "a"}, {"id": "b"}]}
    judged = grade("de_het", sort, {"bins": {"a": "de", "b": "het"}}, {"bins": {"a": "de", "b": "de"}})
    assert judged.outcome == "incorrect" and judged.misses == ["b"] and judged.feedback["bins"]["a"]["ok"]
    with pytest.raises(InvalidAnswer):
        grade("de_het", sort, {"bins": {"a": "de", "b": "het"}}, {"bins": {"a": "de"}})


def test_a_sentence_is_built_by_its_words_not_its_tiles():
    prompt = {"tiles": [{"id": i} for i in "abcde"]}
    key = {"order": list("abcde"), "texts": ["de", "man", "ziet", "de", "hond"]}
    assert grade("sentence_builder", prompt, key, {"order": list("dbcae")}).outcome == "correct", "two tiles 'de'"
    wrong = grade("sentence_builder", prompt, key, {"order": list("bacde")})
    assert wrong.outcome == "incorrect" and wrong.feedback["first_difference"] == 0
    with pytest.raises(InvalidAnswer):
        grade("sentence_builder", prompt, key, {"order": list("abcd")})


def test_one_neighbouring_swap_in_an_ordering_is_almost():
    prompt = {"sentences": [{"id": i} for i in "abcd"]}
    key = {"order": list("abcd"), "texts": ["1", "2", "3", "4"]}
    assert grade("sentence_order", prompt, key, {"order": list("abcd")}).outcome == "correct"
    assert grade("sentence_order", prompt, key, {"order": list("acbd")}).outcome == "almost"
    assert grade("sentence_order", prompt, key, {"order": list("dbca")}).outcome == "incorrect"


def test_a_flashcard_is_the_learners_own_say():
    assert grade("flashcard", {}, {}, {"known": True}).outcome == "correct"
    assert grade("flashcard", {}, {}, {"known": False}).misses == []
    with pytest.raises(InvalidAnswer):
        grade("flashcard", {}, {}, {})


def _session_with(client, kind, *, stage_id="a1"):
    """The first of a few seeded sessions that holds an item of `kind`. Typed kinds come once words are known,
    so the learner first saves a dozen words of the stage."""
    for word in pool_for(stage_id).words[:12]:
        client.post("/words", headers=auth_headers(), json={"term": word.term, "meaning_en": word.meaning["en"]})
    for n in range(30):
        view = client.post("/exercises/sessions", headers=auth_headers(),
                           json={"request_id": f"kinds-{kind[:10]}-{n:04d}", "stage_id": stage_id,
                                 "fresh": True}).json()
        item = next((entry for entry in view["items"] if entry["kind"] == kind), None)
        if item:
            return view, item
    raise AssertionError(f"no {kind} item in 30 sessions")


def _post(client, view, item, action, request_id, **body):
    return client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}", headers=auth_headers(),
                       json={"request_id": request_id, **body})


def _key(item):
    with session_scope() as session:
        return session.scalar(select(ExerciseItem.key).where(ExerciseItem.id == uuid.UUID(item["id"])))


def test_a_typed_answer_can_be_overruled_and_it_completes_nothing(client):
    view, item = _session_with(client, "typed_recall")
    assert set(item["prompt"]) == {"kind", "cue", "hint"} and "accepted" not in str(item["prompt"])
    wrong = _post(client, view, item, "answer", "typed-wrong-0001", answer={"text": "zzzz"}).json()
    assert wrong["outcome"] == "incorrect" and wrong["feedback"]["overridable"] and wrong["feedback"]["expected"]
    accepted = _post(client, view, item, "override", "typed-overr-0001").json()
    assert (accepted["outcome"], accepted["closed"], accepted["points"]) == ("accepted", True, 0)
    assert _post(client, view, item, "override", "typed-overr-0002").json() == accepted, "said once"
    choice = next(entry for entry in view["items"] if entry["kind"] == "choice")
    _post(client, view, choice, "answer", "typed-choice-001", answer={"option": choice["prompt"]["options"][0]["id"]})
    assert _post(client, view, choice, "override", "typed-overr-0003").status_code == 422
    finished = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                           json={"request_id": "typed-finish-01", "early": True}).json()
    assert finished["summary"]["overridden"] == 1
    assert all(missed["ref"] != _key(item)["refs"]["answer"] for missed in finished["summary"]["missed"])
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(TopicPractice)) == 0


def test_an_almost_closes_the_item_without_a_mistake(client):
    view, item = _session_with(client, "typed_recall")
    answer = _key(item)["accepted"][0]
    slip = answer[:-2] + answer[-1] + answer[-2] if len(answer.split()[-1]) >= 4 else answer.upper()
    reply = _post(client, view, item, "answer", "typed-almost-001", answer={"text": slip}).json()
    assert reply["outcome"] in ("almost", "correct") and reply["closed"] and reply["points"] == 1
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(LearnerMistake)) == 0


def test_a_board_is_answered_whole_and_writes_a_mistake_per_missed_word(client):
    client.post("/words", headers=auth_headers(), json={"term": "de ochtend", "meaning_en": "morning"})
    view, item = _session_with(client, "match_pairs")
    key = _key(item)
    left = [entry["id"] for entry in item["prompt"]["left"]]
    rights = [key["pairs"][i] for i in left]
    swapped = dict(zip(left, [rights[1], rights[0], *rights[2:]], strict=True))
    reply = _post(client, view, item, "answer", "board-pairs-0001", answer={"pairs": swapped}).json()
    assert reply["outcome"] == "incorrect" and reply["requeue"] and reply["points"] == 1
    results = reply["feedback"]["pairs"]
    assert [results[i]["ok"] for i in left] == [False, False, True, True]
    assert reply["feedback"]["cards"][left[0]]["term"]
    with session_scope() as session:
        rows = list(session.scalars(select(LearnerMistake)))
    met = {i for i in left[:2] if key["words"][i] in key["met"]}
    assert {row.source_id for row in rows} == {f"{item['id']}:{i}" for i in met}
    incomplete = _post(client, view, item, "answer", "board-pairs-0002", answer={"pairs": {left[0]: rights[0]}})
    assert incomplete.status_code == 422
