"""Items of the first kinds, built from a stage's pool by one seeded random generator.

Each generator returns a `Draft`: the `prompt` the browser may see before answering (opaque option ids, Dutch
options as Dutch only, no answer) and the `key` that stays on the server (the correct option, every option's
glosses, the word card, an explanation). The kinds:

- choice: a word and four options. Directions: Dutch word to its meaning ("meaning"), meaning to the Dutch
  word ("term"), and from A2 the Dutch definition ("definition"). An authored comprehension question keeps
  its own two or three options, shuffled ("question").
- cloze_choice: the word's example sentence with the word blanked, its translation as the cue, and four words
  to fill it (pool.py has the distractor rules).
- odd_one_out: three words of one situation and one word class, and one from a distant topic of another theme
  (pre-A1 to B1).
- intro: the ungraded "nieuwe woorden" card before a session's first new word.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from dlp.domains.curriculum.schemas import Question
from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.pool import DISTRACTORS, Pool, Word, contains_word

GENERATOR_VERSION = "ex-v1"
_ID_LETTERS = "abcdefghjkmnpqrstuvwxyz"


@dataclass
class Draft:
    kind: str
    ref: str
    prompt: dict[str, Any]
    key: dict[str, Any]
    word: str = ""  # the word across stages (Word.key)
    skill: str = ""
    words: tuple[str, ...] = field(default=())  # library ids the item is about


def option_ids(rng: random.Random, count: int) -> list[str]:
    """Opaque, distinct ids: nothing about an option's position or correctness can be read from its id."""
    ids: list[str] = []
    while len(ids) < count:
        candidate = "".join(rng.choice(_ID_LETTERS) for _ in range(4))
        if candidate not in ids:
            ids.append(candidate)
    return ids


def word_card(word: Word) -> dict[str, Any]:
    return {"library_id": word.id, "term": word.term, "meaning": word.meaning, "example": word.example}


def _option_words(ids: list[str], words: list[Word]) -> dict[str, dict[str, str]]:
    """Per option: the word across stages (for 'met') and its library ref (a mistake names the chosen word)."""
    return {"words": {i: w.key for i, w in zip(ids, words, strict=True)},
            "refs": {i: f"word:{w.id}" for i, w in zip(ids, words, strict=True)}}


def _support(option_id: str, word: Word) -> dict[str, str]:
    return {"id": option_id, "nl": word.term, "en": word.meaning["en"], "fa": word.meaning["fa"]}


def distractors(pool: Pool, word: Word, rng: random.Random, candidates: tuple[str, ...]) -> list[Word] | None:
    """Three candidates that differ from each other in every language, drawn at random: nouns for a noun and
    other words for other words first (a verb among nouns gives itself away), then the same topic first."""
    noun = bool(word.article)
    groups: list[list[Word]] = [[], [], [], []]
    for candidate in (pool.by_id[i] for i in candidates):
        groups[(bool(candidate.article) != noun) * 2 + (candidate.topic != word.topic)].append(candidate)
    for group in groups:
        rng.shuffle(group)
    chosen: list[Word] = []
    for candidate in (candidate for group in groups for candidate in group):
        if all(candidate.key != c.key and candidate.core != c.core and not candidate.senses & c.senses
               for c in chosen):
            chosen.append(candidate)
        if len(chosen) == DISTRACTORS:
            return chosen
    return None


def directions(pool: Pool) -> tuple[str, ...]:
    return ("meaning", "term", "definition") if pool.definitions else ("meaning", "term")


def word_choice(pool: Pool, word: Word, rng: random.Random, direction: str) -> Draft | None:
    if direction == "definition" and contains_word(word.meaning["nl"], word.core):
        return None  # "bal waarmee je voetbal speelt" would answer "de voetbal"
    candidates = pool.choice.get(word.id)
    others = distractors(pool, word, rng, candidates) if candidates else None
    if others is None:
        return None
    words = [word, *others]
    rng.shuffle(words)
    ids = option_ids(rng, len(words))
    if direction == "meaning":
        stem = {"nl": word.term}
        options = [{"id": i, "en": w.meaning["en"], "fa": w.meaning["fa"]} for i, w in zip(ids, words, strict=True)]
    elif direction == "term":
        stem = {"en": word.meaning["en"], "fa": word.meaning["fa"]}
        options = [{"id": i, "nl": w.term} for i, w in zip(ids, words, strict=True)]
    elif direction == "definition":
        stem = {"nl": word.term}
        options = [{"id": i, "nl": w.meaning["nl"]} for i, w in zip(ids, words, strict=True)]
    else:
        raise ValueError(f"unknown choice direction {direction}")
    answer = ids[words.index(word)]
    support = [{**_support(i, w), **({"definition": w.meaning["nl"]} if direction == "definition" else {})}
               for i, w in zip(ids, words, strict=True)]
    return Draft(kind="choice", ref=f"word:{word.id}", word=word.key, words=tuple(w.id for w in words),
                 prompt={"kind": "choice", "direction": direction, "stem": stem, "options": options},
                 key={"answer": answer, "support": support, "word": word_card(word), **_option_words(ids, words)})


def authored_choice(question: Question, rng: random.Random, *, skill: str) -> Draft:
    """An authored comprehension question keeps its options, shuffled under opaque ids; their glosses and the
    explanation stay in the key until it is answered."""
    order = list(range(len(question.options)))
    rng.shuffle(order)
    ids = option_ids(rng, len(order))
    options = [{"id": i, "nl": question.options[o].nl} for i, o in zip(ids, order, strict=True)]
    support = [{"id": i, **question.options[o].model_dump()} for i, o in zip(ids, order, strict=True)]
    return Draft(kind="choice", ref=f"question:{question.id}", skill=skill,
                 prompt={"kind": "choice", "direction": "question", "stem": question.prompt.model_dump(),
                         "options": options},
                 key={"answer": ids[order.index(question.answer_index)], "support": support,
                      "explanation": question.explanation.model_dump(), "authored": True})


def cloze_choice(pool: Pool, word: Word, rng: random.Random) -> Draft | None:
    card = pool.cloze.get(word.id)
    if card is None:
        return None
    picked = distractors(pool, word, rng, card.distractors)
    if picked is None:
        return None
    words = [word, *picked]
    rng.shuffle(words)
    ids = option_ids(rng, len(words))
    cue = {"en": word.example["en"], "fa": word.example["fa"]}
    return Draft(kind="cloze_choice", ref=f"word:{word.id}", word=word.key, words=tuple(w.id for w in words),
                 prompt={"kind": "cloze_choice", "sentence": card.sentence, "cue": cue,
                         "options": [{"id": i, "nl": w.core} for i, w in zip(ids, words, strict=True)]},
                 key={"answer": ids[words.index(word)], "support": [_support(i, w) for i, w in zip(ids, words,
                                                                                                   strict=True)],
                      "word": word_card(word), "sentence": word.example["nl"], **_option_words(ids, words)})


def odd_one_out(pool: Pool, group: list[Word], rng: random.Random) -> Draft | None:
    """Three words of one situation and one word class, and one word of that class from a far topic of another
    theme. Never the word that names the situation ('koken' among the words of Koken)."""
    if len(group) != 3 or len({w.topic for w in group}) != 1 or len({bool(w.article) for w in group}) != 1:
        raise ValueError("odd one out needs three words of one topic and one word class")
    topic, noun = group[0].topic, bool(group[0].article)
    label = {token for text in group[0].topic_label.values() for token in fold(text).split()}
    # one word class, or 'the one without de/het' would give the odd word away
    far = [w for t in pool.far_topics(topic) for w in pool.by_topic[t]
           if bool(w.article) == noun and w.core not in label and w.key not in label
           and all(w.key != g.key and w.core != g.core and not w.senses & g.senses for g in group)]
    if not far:
        return None
    odd = rng.choice(far)
    words = [*group, odd]
    rng.shuffle(words)
    ids = option_ids(rng, len(words))
    # the odd word comes from a topic the learner may not know: answering does not make it a word met
    return Draft(kind="odd_one_out", ref=f"word:{odd.id}", words=tuple(w.id for w in words),
                 prompt={"kind": "odd_one_out", "topic": group[0].topic_label,
                         "options": [{"id": i, "nl": w.term} for i, w in zip(ids, words, strict=True)]},
                 key={"answer": ids[words.index(odd)], "support": [_support(i, w) for i, w in zip(ids, words,
                                                                                                strict=True)],
                      "odd_topic": odd.topic_label, "word": word_card(odd), **_option_words(ids, words)})


def intro(stage_id: str, words: list[Word]) -> Draft:
    """The new words of a session, shown before they are practised; nothing to answer."""
    return Draft(kind="intro", ref=f"intro:{stage_id}", words=tuple(w.id for w in words),
                 prompt={"kind": "intro", "words": [{"term": w.term, "meaning": w.meaning, "example": w.example}
                                                    for w in words]},
                 key={})
