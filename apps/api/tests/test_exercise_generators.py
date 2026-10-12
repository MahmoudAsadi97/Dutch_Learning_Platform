"""The exercise generators over the real content: the content gate per stage, and what 200 seeded sessions per
stage must never do (an answer in a prompt, a cloze without its cue, an odd word that gives itself away, ...)."""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from types import SimpleNamespace

import pytest

from dlp.domains.curriculum.library import LibraryWord, library_for
from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question
from dlp.domains.exercises import audio, blueprints, generators, pool
from dlp.domains.exercises.pool import ODD_TOPIC_DISTANCE, build, contains_word, gives_away, pool_for
from dlp.domains.exercises.themes import THEMES, related

# stage -> (words, words with a four-option choice, cloze cards, topics odd one out can use, distinct example
#           sentences, distinct sentence frames, words new against the earlier stages); measured 12 Oct 2026,
#           including source packs. The original reused lists are still labelled as review in roadmap step 3.9;
#           source additions are counted rather than concealed by the content gate.
RECORDED = {
    "pre-a1": (501, 501, 100, 100, 201, 495, 501),
    "a1": (502, 502, 92, 100, 202, 497, 2),
    "pre-a2": (500, 500, 87, 100, 200, 496, 0),
    "a2": (505, 505, 422, 51, 505, 84, 409),
    "pre-b1": (500, 500, 419, 50, 500, 84, 19),
    "b1": (504, 504, 417, 51, 504, 87, 1),
    "pre-b2": (500, 500, 429, 0, 500, 446, 434),
    "b2": (500, 500, 423, 0, 500, 447, 0),
    "pre-c1": (500, 500, 409, 0, 500, 446, 0),
    "c1": (500, 500, 485, 0, 500, 499, 402),
    "pre-c2": (500, 500, 484, 0, 500, 500, 245),
    "c2": (500, 500, 485, 0, 500, 499, 0),
}
SEEDS = 200


def test_every_stage_is_recorded_and_passes_the_content_gate():
    assert list(RECORDED) == list(STAGE_IDS)
    seen: set[str] = set()
    for stage_id, row in RECORDED.items():
        stage = pool_for(stage_id)
        variety = stage.variety
        keys = {word.key for word in stage.words}
        measured = (variety.words, variety.choice, variety.cloze, variety.odd_one_out, variety.examples,
                    variety.frames, len(keys - seen))
        seen |= keys
        assert measured == row, f"{stage_id}: content changed; re-measure and update RECORDED on purpose"
        assert variety.enabled, f"{stage_id} falls below the variety threshold"


@pytest.mark.parametrize("name", ["VARIETY_MIN_CHOICE_WORDS", "VARIETY_MIN_EXAMPLES", "KIND_MIN_ITEMS"])
def test_a_thin_stage_is_kept_out(monkeypatch, name):
    bank = library_for("a1")
    variety = build(bank).variety
    assert variety.enabled
    # Stay exactly one above the measured boundary when additive packs increase the live bank. This still
    # tests each gate independently; production thresholds are never reduced to make a thin stage pass.
    kind_counts = sorted((variety.choice, variety.cloze, variety.odd_one_out), reverse=True)
    value = {"VARIETY_MIN_CHOICE_WORDS": variety.choice + 1,
             "VARIETY_MIN_EXAMPLES": variety.examples + 1,
             "KIND_MIN_ITEMS": kind_counts[pool.VARIETY_MIN_KINDS - 1] + 1}[name]
    monkeypatch.setattr(pool, name, value)
    assert not build(bank).variety.enabled


def test_every_theme_names_topics_that_exist():
    labels = {topic for stage_id in STAGE_IDS for topic in pool_for(stage_id).topics}
    assert set().union(*THEMES) <= labels


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


SECRET_KEYS = {"answer", "support", "explanation", "met", "words", "word", "definition", "refs", "accepted", "pairs",
               "order", "texts", "cards", "translation"}


def _check_board(stage, draft):
    """Boards: every piece has an id that says nothing, and the pieces are never shown solved."""
    prompt, key = draft.prompt, draft.key
    assert not _keys(prompt) & (SECRET_KEYS - {"bins"})
    if draft.kind == "match_pairs":
        assert [o["id"] for o in prompt["right"]] != [key["pairs"][o["id"]] for o in prompt["left"]], "served solved"
        assert len(prompt["left"]) == len(prompt["right"]) == 4
    if draft.kind == "de_het":
        articles = [key["bins"][o["id"]] for o in prompt["options"]]
        assert sorted(articles) == ["de", "de", "de", "het", "het", "het"], "half het, so 'always de' scores half"
        assert not any(o["nl"].split()[0] in ("de", "het", "een") for o in prompt["options"])
    if draft.kind in ("sentence_builder", "sentence_order"):
        pieces = prompt["tiles"] if draft.kind == "sentence_builder" else prompt["sentences"]
        assert [piece["nl"].lower() for piece in pieces] != [text.lower() for text in key["texts"]], "served solved"
        assert sorted(piece["nl"] for piece in pieces) == sorted(key["texts"])
    if draft.kind == "sentence_builder":
        target = stage.by_id[draft.ref.removeprefix("sentence:")]
        assert pool.word_pattern(target.core).search(key["sentence"])


def _check_typed(stage, draft):
    prompt, key = draft.prompt, draft.key
    assert not _keys(prompt) & SECRET_KEYS
    target = stage.by_id[draft.ref.removeprefix("word:")]
    answer = key["accepted"][0] if draft.kind == "cloze_typed" else target.core
    assert prompt["hint"]["letters"] == [sum(char.isalpha() for char in word) for word in answer.split()]
    if draft.kind == "cloze_typed":
        assert prompt["sentence"].count("___") == 1 and not pool.word_pattern(target.core).search(prompt["sentence"])
        assert prompt["cue"] and not gives_away(target)
    else:
        assert target.term in key["accepted"] and prompt["cue"] == {"en": target.meaning["en"],
                                                                     "fa": target.meaning["fa"]}


def _check_prompt(stage, draft):
    """What the browser sees: options with ids that say nothing, Dutch options in Dutch only, no answer."""
    if draft.kind in ("match_pairs", "de_het", "sentence_builder", "sentence_order"):
        return _check_board(stage, draft)
    if draft.kind in ("cloze_typed", "typed_recall"):
        return _check_typed(stage, draft)
    if draft.kind in ("dictation", "shadow"):
        assert not _keys(draft.prompt) & SECRET_KEYS
        if draft.kind == "dictation":
            assert draft.key["audio_text"] not in str(draft.prompt), "a dictation never shows what it says"
        return None
    prompt, key = draft.prompt, draft.key
    assert not _keys(prompt) & SECRET_KEYS
    ids = [option["id"] for option in prompt["options"]]
    assert len(set(ids)) == len(ids) == 4 and all(re.fullmatch(r"[a-z]{4}", i) for i in ids)
    assert key["answer"] in ids and set(key["refs"]) == set(ids)
    for lang in ("nl", "en", "fa"):
        shown = [option[lang] for option in prompt["options"] if lang in option]
        assert len(set(shown)) == len(shown), f"two options read the same in {lang}"
    dutch_options = draft.kind != "choice" or prompt["direction"] in ("term", "definition")
    for option in prompt["options"]:
        assert set(option) == ({"id", "nl"} if dutch_options else {"id", "en", "fa"})
    target = stage.by_id[key["refs"][key["answer"]].removeprefix("word:")]
    if draft.kind == "choice" and prompt["direction"] == "definition":
        assert not contains_word(target.meaning["nl"], target.core), "the definition names the word"
    if draft.kind == "cloze_choice":
        sentence = prompt["sentence"]
        assert sentence.count("___") == 1 and not pool.word_pattern(target.core).search(sentence)
        assert prompt["cue"] == {"en": target.example["en"], "fa": target.example["fa"]}, "every cloze has its cue"
        assert not gives_away(target)
        others = [stage.by_id[ref.removeprefix("word:")] for ref in key["refs"].values() if ref != draft.ref]
        assert all(other.article == target.article for other in others)
        assert not any(pool.word_pattern(other.core).search(target.example["nl"]) for other in others)
    if draft.kind == "odd_one_out":
        words = [stage.by_id[ref.removeprefix("word:")] for ref in key["refs"].values()]
        group = [w for w in words if w.id != target.id]
        assert len({w.topic for w in group}) == 1 and prompt["topic"]["nl"] == group[0].topic
        assert abs(target.topic_index - group[0].topic_index) >= ODD_TOPIC_DISTANCE
        assert not related(group[0].topic, target.topic), "a word of the same theme is not odd"
        assert len({bool(w.article) for w in words}) == 1, "the odd word has the group's word class"


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_two_hundred_sessions_per_stage_keep_the_rules(stage_id):
    stage = pool_for(stage_id)
    kinds: set[str] = set()
    for seed in range(SEEDS):
        rng = random.Random(seed)
        known = frozenset(word.key for word in rng.sample(stage.words, (seed % 25) * 12))
        size = blueprints.SIZE_MIN + seed % (blueprints.SIZE_MAX - blueprints.SIZE_MIN + 1)
        topic = rng.choice(stage.topics) if seed % 4 == 0 else None
        speech = seed % 2 == 0
        drafts = blueprints.plan(stage, random.Random(f"{stage_id}:{seed}"), size=size, met=known,
                                 library_topic=topic, audio=speech)
        again = blueprints.plan(stage, random.Random(f"{stage_id}:{seed}"), size=size, met=known,
                                library_topic=topic, audio=speech)
        assert [(d.ref, d.prompt) for d in drafts] == [(d.ref, d.prompt) for d in again], "seeded"
        graded = [d for d in drafts if d.kind != "intro"]
        assert 1 <= len(graded) <= size and (topic or len(graded) == size)
        intro = drafts[0] if drafts[0].kind == "intro" else None
        new = set(intro.words if intro else ())
        assert all(stage.by_id[word_id].key not in known for word_id in new)
        assert all(d.kind != "intro" for d in drafts[1:])
        practised = set().union(*(blueprints._targets(d) for d in graded))
        assert new <= practised, "every new word on the intro card is practised"
        assert {i for i in practised if stage.by_id[i].key not in known} <= new, "every new word practised is introduced"
        examples = " ".join(stage.by_id[d.ref.split(":", 1)[1]].example["nl"].lower() for d in graded
                            if d.ref.startswith(("word:", "sentence:")))
        for board in (d for d in graded if d.kind == "sentence_order"):
            assert not any(text.lower() in examples for text in board.key["texts"]), "no other item shows its order"
        clozes = [stage.by_id[d.ref.split(":", 1)[1]] for d in graded if d.kind in blueprints.EXAMPLE_KINDS]
        assert len({w.example["nl"] for w in clozes}) == len({w.frame for w in clozes}) == len(clozes), (
            "one cloze per example and per sentence frame")
        for word in clozes:
            assert not any(pool.word_pattern(word.core).search(other.example["nl"]) for other in clozes
                           if other.id != word.id), "a cloze answer stands in another cloze"
        firsts: dict[str, str] = {}
        for draft in graded:
            kinds.add(draft.kind)
            _check_prompt(stage, draft)
            firsts.setdefault(draft.ref, draft.prompt.get("direction", draft.kind))
            if draft.word:
                assert (draft.word in draft.key["met"]) == (draft.word in known)
        for word_id in new:
            assert firsts.get(f"word:{word_id}") == "meaning", "a new word is first recognised"
        counts = Counter(d.word for d in graded if d.word)
        if not counts or max(counts.values()) * 2 <= len(graded) + 1:
            assert all(a.word != b.word for a, b in zip(graded, graded[1:], strict=False) if a.word), "spread"
    assert {"choice", "cloze_choice", "cloze_typed", "typed_recall", "sentence_builder", "match_pairs",
            "listen_choose", "dictation"} <= kinds
    # A uniform sample need not select the four short B1 supplement cards among 504 words. Availability
    # has its own targeted coverage below; this random-session check still refuses unavailable shadow items.
    if "shadow" in kinds:
        assert any(audio.shadow(stage, word) for word in stage.words)
    assert ("odd_one_out" in kinds) == stage.odd_one_out
    assert ("de_het" in kinds) == bool(stage.sortable)
    assert ("sentence_order" in kinds) == bool(stage.orders)


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_available_shadow_is_planned_in_a_targeted_topic(stage_id):
    stage = pool_for(stage_id)
    eligible = {topic: sum(word.id in stage.shadowed for word in stage.by_topic[topic])
                / len(stage.by_topic[topic]) for topic in stage.topics}
    topic = max(eligible, key=eligible.get)
    assert eligible[topic] > 0, "the recorded catalog has a short speaking example in every stage"
    met = frozenset(word.key for word in stage.words)
    shadows = []
    for seed in range(60):
        drafts = blueprints.plan(stage, random.Random(f"{stage_id}:shadow:{seed}"), size=12, met=met,
                                 library_topic=topic, audio=True)
        for draft in drafts:
            _check_prompt(stage, draft)
        shadows.extend(draft for draft in drafts if draft.kind == "shadow")
        if shadows:
            break
    assert shadows, f"{stage_id}: available shadow cards must be reachable through real topic planning"
    for draft in shadows:
        word = stage.by_id[draft.ref.removeprefix("word:")]
        assert word.topic == topic
        assert draft.prompt["sentence"] == draft.key["audio_text"] == stage.shadowed[word.id]
        assert draft.skill == "speaking"


@pytest.mark.parametrize("stage_id", ["a1", "b2"])
def test_a_while_you_wait_session_is_tapped_only(stage_id):
    stage = pool_for(stage_id)
    met = frozenset(word.key for word in stage.words)
    for seed in range(50):
        drafts = blueprints.plan(stage, random.Random(seed), size=5, met=met, typing=False)
        assert not {d.kind for d in drafts} & {"cloze_typed", "typed_recall"}


def test_a_topic_session_stays_in_its_topic():
    stage = pool_for("a1")
    topic = stage.topics[3]
    drafts = blueprints.plan(stage, random.Random("topic"), size=8, met=frozenset(), library_topic=topic)
    assert {stage.by_id[i].topic for d in drafts if d.kind == "intro" for i in d.words} == {topic}
    # de/het may also sort nouns the learner met elsewhere; here nothing was met
    practised = set().union(*(blueprints._targets(d) for d in drafts if d.kind != "intro"))
    assert {stage.by_id[i].topic for i in practised} == {topic}


def test_spreading_keeps_each_word_apart_and_its_own_order():
    def draft(word, n):
        return generators.Draft(kind="choice", ref=f"word:{word}", prompt={"n": n}, key={}, word=word)

    order = blueprints._spread([draft("a", 1), draft("a", 2), draft("c", 1), draft("a", 3), draft("d", 1)])
    assert [d.word for d in order] == ["a", "c", "a", "d", "a"]
    assert [d.prompt["n"] for d in order if d.word == "a"] == [1, 2, 3]
    tail = blueprints._spread([draft("a", 1), draft("b", 1), draft("c", 1), draft("d", 1), draft("d", 2)])
    assert all(x.word != y.word for x, y in zip(tail, tail[1:], strict=False))


def _bank(examples: dict[str, tuple[str, str]]):
    """A stage-shaped bank of one topic: term -> (Dutch example, English translation)."""
    words = [LibraryWord(id=f"w{i}", term=term, topic=Localized(nl="Documenten", en="Documents", fa="مدارک"),
                         meaning=Localized(nl=f"betekenis {i}", en=f"meaning {i}", fa=f"معنی {i}"),
                         example=Localized(nl=nl, en=en, fa=f"مثال {i}"))
             for i, (term, (nl, en)) in enumerate(examples.items())]
    return SimpleNamespace(stage_id="a2", vocabulary=words, model_dump_json=lambda: "bank")


def test_a_cloze_always_shows_its_translation_unless_it_shows_the_word():
    stage = build(_bank({
        "het paspoort": ("Ik leg mijn paspoort klaar.", "I get my passport ready."),
        "het formulier": ("Ik leg mijn formulier klaar.", "I get my form ready."),
        "het attest": ("Ik leg mijn attest klaar.", "I get my certificate ready."),
        "het contract": ("Ik leg mijn contract klaar.", "I get my agreement ready."),
        "het diploma": ("Ik leg mijn diploma klaar.", "I get my diploma ready."),
        "een e-mail": ("Ik stuur een e-mail.", "I send an email."),
        "de yogamat": ("Ik leen de yogamat.", "I borrow the yoga mat."),
        "de offerte": ("Twee offertes kwamen binnen; de goedkoopste offerte won.", "Two quotes came in."),
    }))
    assert stage.cloze["w0"].sentence == "Ik leg mijn ___ klaar."
    draft = generators.cloze_choice(stage, stage.by_id["w0"], random.Random(1))
    assert draft.prompt["cue"] == {"en": "I get my passport ready.", "fa": "مثال 0"}
    for given_away in ("w4", "w5", "w6"):  # diploma, email, yoga mat
        assert given_away not in stage.cloze
    assert stage.by_id["w7"].span is None, "another form of the word stands in the sentence"


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
        # each option's place in the authored list stays in the key, so a first answer can be checked by the
        # course's own rule; the ref names the question unless the caller qualifies it (a lesson's ids repeat)
        assert draft.key["question"] == "a1-t001-r1" and draft.ref == "question:a1-t001-r1"
        assert draft.key["positions"][draft.key["answer"]] == question.answer_index
        assert sorted(draft.key["positions"].values()) == [0, 1]
    assert positions == {0, 1}
    lesson = generators.authored_choice(question, random.Random(0), skill="reading", ref="question:a1:r1")
    assert lesson.ref == "question:a1:r1"
