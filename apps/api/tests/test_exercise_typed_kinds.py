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
from dlp.domains.exercises.typed import typed_recall
from tests.conftest import auth_headers

# stage -> (words with a typed cloze, words with a typed recall (not a word its meaning spells), nouns to sort
#           into de/het (never one that takes both articles), words with a sentence to build, paragraphs to put in
#           order); the other kinds work for every word. Measured 16 Oct 2026 including source and connected packs.
AVAILABLE = {
    'pre-a1': (461, 471, 303, 108, 0),
    'a1': (462, 473, 307, 188, 0),
    'pre-a2': (456, 463, 304, 140, 0),
    'a2': (483, 488, 320, 368, 0),
    'pre-b1': (488, 499, 338, 149, 139),
    'b1': (491, 504, 342, 115, 100),
    'pre-b2': (463, 528, 401, 240, 122),
    'b2': (455, 525, 400, 239, 214),
    'pre-c1': (460, 560, 402, 262, 228),
    'c1': (561, 565, 0, 272, 226),
    'pre-c2': (525, 579, 0, 241, 241),
    'c2': (564, 571, 0, 263, 229),
}


def test_which_stage_has_which_kind():
    assert list(AVAILABLE) == list(STAGE_IDS)
    for stage_id, row in AVAILABLE.items():
        available = pool_for(stage_id).available()
        measured = (available["cloze_typed"], available["typed_recall"], available["de_het"],
                    available["sentence_builder"], available["sentence_order"])
        assert measured == row, f"{stage_id}: content changed; re-measure and update AVAILABLE on purpose"


def test_no_noun_that_takes_both_articles_is_sorted():
    sortable = {pool_for(stage_id).by_id[i].core for stage_id in STAGE_IDS for i in pool_for(stage_id).sortable}
    assert not sortable & {"punt", "pad", "bal", "doek", "bos", "rooster", "band", "matras"}


@pytest.fixture(autouse=True)
def _no_speech(settings, monkeypatch):
    """These sessions run without the kinds that speak (the audio allowance below the planning threshold);
    tests/test_exercises_audio.py covers those."""
    monkeypatch.setattr(settings, "usage_daily_audio_seconds", 30)


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


def test_a_word_from_the_cue_is_another_word_and_a_synonym_needs_every_gloss():
    key = {"accepted": ["thee"], "article": "none", "cue_words": ["there", "is", "coffee", "tea", "and", "milk"]}
    assert grade("cloze_typed", {}, key, {"text": "There"}).outcome == "incorrect", "copied from the cue"
    assert grade("cloze_typed", {}, key, {"text": "thea"}).outcome == "almost"
    stage = pool_for("pre-a1")
    deur = next(word for word in stage.words if word.term == "de deur")
    assert typed_recall(stage, deur).key["accepted"] == ["de deur"], "'in' shares only a Persian gloss"
    bed = next(word for word in stage.words if word.term == "het bed")
    assert typed_recall(stage, bed) is None, "the cue 'bed' would be the answer"


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
    assert grade("sentence_order", prompt, key, {"order": list("dabc")}).outcome == "almost", "the closing line first"
    assert grade("sentence_order", prompt, key, {"order": list("dbca")}).outcome == "incorrect"


def test_a_flashcard_is_the_learners_own_say():
    assert grade("flashcard", {}, {}, {"known": True}).outcome == "correct"
    assert grade("flashcard", {}, {}, {"known": False}).misses == []
    with pytest.raises(InvalidAnswer):
        grade("flashcard", {}, {}, {})


def _session_with(client, kind, *, stage_id="a1", where=lambda item, key: True):
    """The first of a few seeded sessions that holds an item of `kind` (meeting `where`). Typed kinds come once
    words are known, so the learner first saves a dozen words of the stage."""
    for word in pool_for(stage_id).words[:12]:
        client.post("/words", headers=auth_headers(), json={"term": word.term, "meaning_en": word.meaning["en"]})
    for n in range(40):
        view = client.post("/exercises/sessions", headers=auth_headers(),
                           json={"request_id": f"kinds-{kind[:10]}-{n:04d}", "stage_id": stage_id,
                                 "fresh": True}).json()
        item = next((entry for entry in view["items"] if entry["kind"] == kind and where(entry, _key(entry))), None)
        if item:
            return view, item
    raise AssertionError(f"no {kind} item in 40 sessions")


def _post(client, view, item, action, request_id, **body):
    return client.post(f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}", headers=auth_headers(),
                       json={"request_id": request_id, **body})


def _key(item):
    with session_scope() as session:
        return session.scalar(select(ExerciseItem.key).where(ExerciseItem.id == uuid.UUID(item["id"])))


def _mistakes() -> set[str]:
    with session_scope() as session:
        return set(session.scalars(select(LearnerMistake.source_id)))


def _met(item, key) -> bool:
    return key["words"]["answer"] in key["met"]


def test_a_typed_answer_can_be_overruled_and_it_completes_nothing(client):
    view, item = _session_with(client, "typed_recall", where=_met)
    assert set(item["prompt"]) == {"kind", "cue", "hint"} and "accepted" not in str(item["prompt"])
    wrong = _post(client, view, item, "answer", "typed-wrong-0001", answer={"text": "zzzz"}).json()
    assert wrong["outcome"] == "incorrect" and wrong["feedback"]["overridable"] and wrong["feedback"]["expected"]
    assert item["id"] in _mistakes(), "a word met before: the miss is a mistake"
    accepted = _post(client, view, item, "override", "typed-overr-0001").json()
    assert (accepted["outcome"], accepted["closed"], accepted["points"]) == ("accepted", True, 0)
    assert item["id"] not in _mistakes(), "the learner's overrule removes it"
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


def _slip(text: str) -> str:
    """The answer with the second and third letters of its last word swapped: one slip of the keyboard."""
    head, _, last = text.rpartition(" ")
    return (head + " " if head else "") + last[0] + last[2] + last[1] + last[3:]


def _slippable(item, key) -> bool:
    last = key["accepted"][0].split()[-1]
    return _met(item, key) and len(last) >= 5 and last[1] != last[2]


def test_an_almost_closes_the_item_without_a_mistake(client):
    view, item = _session_with(client, "typed_recall", where=_slippable)
    reply = _post(client, view, item, "answer", "typed-almost-001",
                  answer={"text": _slip(_key(item)["accepted"][0])}).json()
    assert (reply["outcome"], reply["closed"], reply["points"]) == ("almost", True, 1)
    assert item["id"] not in _mistakes(), "almost is never a mistake, also on a word met before"


def _two_met(item, key) -> bool:
    return sum(key["words"][i] in key["met"] for i in key["pairs"]) >= 2


def test_a_board_is_answered_whole_and_writes_a_mistake_per_missed_word(client):
    view, item = _session_with(client, "match_pairs", where=_two_met)
    key = _key(item)
    met = [i for i in key["pairs"] if key["words"][i] in key["met"]][:2]
    pairs = dict(key["pairs"])
    pairs[met[0]], pairs[met[1]] = key["pairs"][met[1]], key["pairs"][met[0]]
    reply = _post(client, view, item, "answer", "board-pairs-0001", answer={"pairs": pairs}).json()
    assert reply["outcome"] == "incorrect" and reply["requeue"] and reply["points"] == 1
    results = reply["feedback"]["pairs"]
    assert sorted(i for i, result in results.items() if not result["ok"]) == sorted(met)
    assert reply["feedback"]["cards"][met[0]]["term"]
    assert _mistakes() == {f"{item['id']}:{i}" for i in met}, "one mistake per missed word"
    incomplete = _post(client, view, item, "answer", "board-pairs-0002", answer={"pairs": {met[0]: pairs[met[0]]}})
    assert incomplete.status_code == 422
    finished = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                           json={"request_id": "board-finish-001", "early": True}).json()
    named = {missed["term"] for missed in finished["summary"]["missed"]}
    assert {key["cards"][i]["term"] for i in met} <= named, "the summary names the words a board missed"
