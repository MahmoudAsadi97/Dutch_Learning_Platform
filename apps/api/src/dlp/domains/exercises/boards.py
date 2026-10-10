"""Items the learner solves as a whole board: match pairs, de/het sorting, sentence building and ordering.

A board is submitted whole (roadmap 3.6) and each part is judged: every pair, every noun, every position.
Pieces carry opaque ids and are shown in an order that is never the solution.
"""
from __future__ import annotations

import random
from typing import Any

from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.generators import Draft, option_ids, word_card
from dlp.domains.exercises.pool import OrderRun, Pool, Word

PAIRS = 4
SORT_NOUNS = 6


def _scrambled(rng: random.Random, items: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
    """A shuffle of (id, piece) pairs that never reads as the original order: two identical pieces swapped
    still read solved, so the pieces are compared by their text."""
    def reads(pairs: list[tuple[str, Any]]) -> list[str]:
        return [fold(piece) if isinstance(piece, str) else id(piece) for _, piece in pairs]

    order = list(items)
    for _ in range(50):
        rng.shuffle(order)
        if reads(order) != reads(items):
            break
    return order


def _per_word(ids: list[str], words: list[Word]) -> dict[str, dict[str, Any]]:
    return {"cards": {i: word_card(word) for i, word in zip(ids, words, strict=True)},
            "words": {i: word.key for i, word in zip(ids, words, strict=True)},
            "refs": {i: f"word:{word.id}" for i, word in zip(ids, words, strict=True)}}


def match_pairs(pool: Pool, words: list[Word], rng: random.Random) -> Draft:
    """Dutch words on the left, their meanings in the support language on the right."""
    if len(words) != PAIRS:
        raise ValueError(f"match pairs needs {PAIRS} words")
    left_ids, right_ids = option_ids(rng, PAIRS), option_ids(rng, PAIRS)
    right = _scrambled(rng, list(zip(right_ids, words, strict=True)))
    return Draft(kind="match_pairs", ref="pairs:" + ":".join(word.id for word in words)[:113],
                 words=tuple(word.id for word in words),
                 prompt={"kind": "match_pairs",
                         "left": [{"id": i, "nl": word.term} for i, word in zip(left_ids, words, strict=True)],
                         "right": [{"id": i, "en": word.meaning["en"], "fa": word.meaning["fa"]} for i, word in right]},
                 key={"pairs": dict(zip(left_ids, right_ids, strict=True)), **_per_word(left_ids, words)})


def de_het(pool: Pool, nouns: list[Word], rng: random.Random) -> Draft:
    """Nouns without their article, to sort into de and het."""
    if len(nouns) != SORT_NOUNS or any(noun.article not in ("de", "het") for noun in nouns):
        raise ValueError(f"de/het needs {SORT_NOUNS} nouns with de or het")
    ids = option_ids(rng, SORT_NOUNS)
    shown = _scrambled(rng, list(zip(ids, nouns, strict=True)))
    return Draft(kind="de_het", ref="article:" + ":".join(noun.id for noun in nouns)[:111],
                 words=tuple(noun.id for noun in nouns),
                 prompt={"kind": "de_het", "bins": ["de", "het"],
                         "options": [{"id": i, "nl": noun.core} for i, noun in shown]},
                 key={"bins": {i: noun.article for i, noun in zip(ids, nouns, strict=True)},
                      **_per_word(ids, nouns)})


def sentence_builder(pool: Pool, word: Word, rng: random.Random) -> Draft | None:
    """A sentence of the word's example, as word tiles or chunks, to put in order."""
    found = pool.pieces.get(word.id)
    if found is None:
        return None
    ids = option_ids(rng, len(found.pieces))
    shown = _scrambled(rng, list(zip(ids, found.pieces, strict=True)))
    return Draft(kind="sentence_builder", ref=f"sentence:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "sentence_builder", "tiles": [{"id": i, "nl": piece} for i, piece in shown],
                         "end": found.end, "cue": found.cue},
                 key={"order": ids, "texts": list(found.pieces), "sentence": found.sentence, "word": word_card(word),
                      "words": {"answer": word.key}, "refs": {"answer": f"word:{word.id}"}})


def sentence_order(run: OrderRun, rng: random.Random) -> Draft:
    """Three or four consecutive sentences of a Story Time paragraph to put back in order."""
    ids = option_ids(rng, len(run.sentences))
    shown = _scrambled(rng, list(zip(ids, run.sentences, strict=True)))
    return Draft(kind="sentence_order", ref=run.ref[:120],
                 prompt={"kind": "sentence_order", "sentences": [{"id": i, "nl": text} for i, text in shown]},
                 key={"order": ids, "texts": list(run.sentences), "translation": dict(run.translation)})
