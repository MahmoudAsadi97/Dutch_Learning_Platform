"""The exercise generators over the real content: the content gate per stage, and what 200 seeded sessions per
stage must never do (an answer in a prompt, a cloze sibling that fits the blank, a repeated sentence, ...)."""
from __future__ import annotations

import json
import random
import re
from types import SimpleNamespace

import pytest

from dlp.domains.curriculum.library import LibraryWord
from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question
from dlp.domains.exercises import blueprints, generators, pool
from dlp.domains.exercises.pool import ODD_TOPIC_DISTANCE, build, pool_for

# stage -> (words, words with a four-option choice, cloze cards, cloze cards with the translation cue,
#           topics odd one out can use); measured 10 Oct 2026 on the content of 6 Oct
RECORDED = {
    "pre-a1": (500, 500, 103, 0, 100),
    "a1": (500, 500, 99, 0, 100),
    "pre-a2": (500, 500, 89, 0, 100),
    "a2": (500, 500, 4, 422, 50),
    "pre-b1": (500, 500, 13, 410, 50),
    "b1": (500, 500, 11, 411, 50),
    "pre-b2": (500, 500, 438, 0, 0),
    "b2": (500, 500, 435, 0, 0),
    "pre-c1": (500, 500, 418, 0, 0),
    "c1": (500, 500, 496, 0, 0),
    "pre-c2": (500, 500, 492, 0, 0),
    "c2": (500, 500, 492, 0, 0),
}
SEEDS = 200


def test_every_stage_is_recorded_and_passes_the_content_gate():
    assert list(RECORDED) == list(STAGE_IDS)
    for stage_id, row in RECORDED.items():
        variety = pool_for(stage_id).variety
        assert (variety.words, variety.choice, variety.cloze, variety.cloze_cued, variety.odd_one_out) == row, (
            f"{stage_id}: content changed; re-measure and update RECORDED on purpose")
        assert variety.enabled, f"{stage_id} falls below the variety threshold"


def test_a_thin_stage_is_kept_out(monkeypatch):
    monkeypatch.setattr(pool, "VARIETY_MIN_CHOICE_WORDS", 501)
    assert not pool_for("a1").variety.enabled


def _contains(text: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", text, re.I) is not None


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def _check_prompt(stage, draft):
    """What the browser sees: options with ids that say nothing, Dutch options in Dutch only, no answer."""
    prompt, key = draft.prompt, draft.key
    assert not _keys(prompt) & {"answer", "support", "explanation", "met", "words", "word", "definition"}
    ids = [option["id"] for option in prompt["options"]]
    assert len(set(ids)) == len(ids) == 4 and all(re.fullmatch(r"[a-z]{4}", i) for i in ids)
    assert key["answer"] in ids
    for lang in ("nl", "en", "fa"):
        shown = [option[lang] for option in prompt["options"] if lang in option]
        assert len(set(shown)) == len(shown), f"two options read the same in {lang}"
    dutch_options = draft.kind != "choice" or prompt["direction"] in ("term", "definition")
    for option in prompt["options"]:
        assert set(option) == ({"id", "nl"} if dutch_options else {"id", "en", "fa"})
    if draft.kind == "cloze_choice":
        target = stage.by_id[draft.ref.removeprefix("word:")]
        sentence = prompt["sentence"]
        assert sentence.count("___") == 1 and not _contains(sentence, target.core)
        if prompt["cue"]:
            assert not any(_contains(prompt["cue"][lang], target.core) for lang in ("en", "fa"))
        others = [stage.by_id[i] for i in draft.words if i != target.id]
        assert all(other.article == target.article for other in others)
        assert not any(_contains(target.example["nl"], other.core) for other in others), "a sibling in the sentence"
        if not prompt["cue"]:
            assert all(other.frame != target.frame for other in others), "a sibling that fits the blank"
    if draft.kind == "odd_one_out":
        words = [stage.by_id[i] for i in draft.words]
        odd = stage.by_id[draft.ref.removeprefix("word:")]
        group = [w for w in words if w.id != odd.id]
        assert len({w.topic for w in group}) == 1 and prompt["topic"]["nl"] == group[0].topic
        assert abs(odd.topic_index - group[0].topic_index) >= ODD_TOPIC_DISTANCE


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_two_hundred_sessions_per_stage_keep_the_rules(stage_id):
    stage = pool_for(stage_id)
    kinds: set[str] = set()
    for seed in range(SEEDS):
        known = frozenset(word.key for word in random.Random(seed).sample(stage.words, (seed % 25) * 12))
        drafts = blueprints.plan(stage, random.Random(f"{stage_id}:{seed}"), size=8, met=known)
        again = blueprints.plan(stage, random.Random(f"{stage_id}:{seed}"), size=8, met=known)
        assert [(d.ref, d.prompt) for d in drafts] == [(d.ref, d.prompt) for d in again], "seeded"
        graded = [d for d in drafts if d.kind != "intro"]
        assert len(graded) == 8
        intro = drafts[0] if drafts[0].kind == "intro" else None
        new = {word_id for word_id in (intro.words if intro else ())}
        assert all(stage.by_id[word_id].key not in known for word_id in new)
        assert all(d.kind != "intro" for d in drafts[1:])
        sentences = [d.prompt["sentence"] for d in graded if d.kind == "cloze_choice"]
        assert len(sentences) == len(set(sentences)), "one cloze per sentence"
        firsts: dict[str, str] = {}
        for draft in graded:
            kinds.add(draft.kind)
            _check_prompt(stage, draft)
            firsts.setdefault(draft.ref, draft.prompt.get("direction", draft.kind))
            if draft.kind != "odd_one_out":
                assert (draft.word in draft.key["met"]) == (draft.word in known)
        for word_id in new:
            assert firsts.get(f"word:{word_id}") == "meaning", "a new word is first recognised"
        assert all(a.word != b.word for a, b in zip(graded, graded[1:], strict=False) if a.word), "spread"
    assert "choice" in kinds and "cloze_choice" in kinds
    assert ("odd_one_out" in kinds) == stage.odd_one_out


def test_a_topic_session_stays_in_its_topic():
    stage = pool_for("a1")
    topic = stage.topics[3]
    drafts = blueprints.plan(stage, random.Random("topic"), size=8, met=frozenset(), library_topic=topic)
    assert {stage.by_id[i].topic for d in drafts if d.kind == "intro" for i in d.words} == {topic}
    assert all(stage.by_id[d.ref.removeprefix("word:")].topic == topic for d in drafts
               if d.kind not in ("intro", "odd_one_out"))


def _bank(examples: dict[str, tuple[str, str]]):
    """A stage-shaped bank of one topic: term -> (Dutch example, English translation)."""
    words = [LibraryWord(id=f"w{i}", term=term, topic=Localized(nl="Documenten", en="Documents", fa="مدارک"),
                         meaning=Localized(nl=f"betekenis {i}", en=f"meaning {i}", fa=f"معنی {i}"),
                         example=Localized(nl=nl, en=en, fa=f"مثال {i}"))
             for i, (term, (nl, en)) in enumerate(examples.items())]
    return SimpleNamespace(stage_id="a2", vocabulary=words, model_dump_json=lambda: "bank")


def test_siblings_that_fit_the_blank_need_the_translation_cue():
    stage = build(_bank({
        "het paspoort": ("Ik leg mijn paspoort klaar.", "I get my passport ready."),
        "het formulier": ("Ik leg mijn formulier klaar.", "I get my form ready."),
        "het attest": ("Ik leg mijn attest klaar.", "I get my certificate ready."),
        "het contract": ("Ik leg mijn contract klaar.", "I get my agreement ready."),
        "het diploma": ("Ik leg mijn diploma klaar.", "I get my diploma ready."),
    }))
    card = stage.cloze["w0"]
    assert card.cued and card.sentence == "Ik leg mijn ___ klaar."
    assert "w4" not in stage.cloze, "the translation shows the Dutch word: no cloze"
    draft = generators.cloze_choice(stage, stage.by_id["w0"], random.Random(1))
    assert draft.prompt["cue"] == {"en": "I get my passport ready.", "fa": "مثال 0"}


def test_authored_questions_keep_their_options_shuffled_under_opaque_ids():
    question = Question(id="a1-t001-r1", prompt=Localized(nl="Waar woont Sara?", en="Where?", fa="کجا؟"),
                        options=[Localized(nl="In Gent", en="In Ghent", fa="در گنت"),
                                 Localized(nl="In Brussel", en="In Brussels", fa="در بروکسل")],
                        answer_index=1, explanation=Localized(nl="Ze woont in Brussel.", en="She lives in Brussels.",
                                                              fa="او در بروکسل زندگی می‌کند."))
    positions = set()
    for seed in range(20):
        draft = generators.authored_choice(question, random.Random(seed), skill="reading")
        options = draft.prompt["options"]
        assert len(options) == 2 and all(set(option) == {"id", "nl"} for option in options)
        answer = next(option for option in options if option["id"] == draft.key["answer"])
        assert answer["nl"] == "In Brussel"
        positions.add(options.index(answer))
        assert "Ze woont" not in json.dumps(draft.prompt, ensure_ascii=False)
        assert draft.key["explanation"]["nl"] == "Ze woont in Brussel." and draft.key["authored"]
    assert positions == {0, 1}
