"""Which words a session practises, with which items, in which order.

A session takes up to NEW_WORDS new words (never practised in an earlier session and not in the word bank)
in library order, and fills the rest with words met before, the least recently practised first; a first
session, with nothing to review yet, introduces up to NEW_WORDS_FIRST. New words are shown on an ungraded
intro card first and first practised by recognition (the Dutch word to its meaning). Every word gets one
item, and further items in another kind or direction until the session has its size. No two cloze items use
the same sentence (one example serves several A1 words), no two items about the same word follow each other,
and one odd-one-out item joins where the stage has it and three words of one situation are known.
"""
from __future__ import annotations

import random
from datetime import UTC, datetime

from dlp.domains.exercises import generators
from dlp.domains.exercises.generators import Draft
from dlp.domains.exercises.pool import Pool, Word

SIZES = {"stage_skill": 8, "while_you_wait": 5}
SIZE_MIN, SIZE_MAX = 5, 12
NEW_WORDS = 4
NEW_WORDS_FIRST = 6
ODD_ONE_OUT_MIN_SIZE = 6
_NEVER = datetime.min.replace(tzinfo=UTC)


def _distinct(words: list[Word], taken: set[str]) -> list[Word]:
    picked: list[Word] = []
    for word in words:
        if word.key not in taken:
            taken.add(word.key)
            picked.append(word)
    return picked


def _item(pool: Pool, word: Word, rng: random.Random, *, used: set[tuple[str, str]],
          sentences: set[str]) -> Draft | None:
    """An item for `word` in a kind or direction it has not had in this session."""
    options: list[tuple[str, str]] = [("choice", direction) for direction in generators.directions(pool)]
    card = pool.cloze.get(word.id)
    if card and card.sentence not in sentences:
        options.append(("cloze_choice", ""))
    rng.shuffle(options)
    for kind, direction in options:
        if (kind, direction) in used:
            continue
        draft = (generators.cloze_choice(pool, word, rng) if kind == "cloze_choice"
                 else generators.word_choice(pool, word, rng, direction))
        if draft is not None:
            used.add((kind, direction))
            if kind == "cloze_choice" and card:
                sentences.add(card.sentence)
            return draft
    return None


def _odd_one_out(pool: Pool, words: list[Word], met: frozenset[str], rng: random.Random) -> Draft | None:
    if not pool.odd_one_out:
        return None
    for topic in dict.fromkeys(word.topic for word in words):
        group = [w for w in words if w.topic == topic]
        group += [w for w in pool.by_topic[topic] if w.key in met and w not in group]
        if len(group) >= 3:
            draft = generators.odd_one_out(pool, group[:3], rng)
            if draft is not None:
                return draft
    return None


def _spread(drafts: list[Draft]) -> list[Draft]:
    """No two items about the same word in a row, where another order allows it."""
    for index in range(1, len(drafts)):
        if drafts[index].word and drafts[index].word == drafts[index - 1].word:
            swap = next((j for j in range(index + 1, len(drafts))
                         if drafts[j].word != drafts[index - 1].word
                         and (j + 1 >= len(drafts) or drafts[j + 1].word != drafts[index].word)), None)
            if swap is not None:
                drafts[index], drafts[swap] = drafts[swap], drafts[index]
    return drafts


def plan(pool: Pool, rng: random.Random, *, size: int, met: frozenset[str],
         last_seen: dict[str, datetime] | None = None, library_topic: str | None = None) -> list[Draft]:
    """The session's drafts in order: the intro card (when there are new words), then the graded items."""
    last_seen = last_seen or {}
    candidates = [w for w in (pool.by_topic[library_topic] if library_topic else pool.words) if w.id in pool.choice]
    new = [w for w in candidates if w.key not in met]
    review = sorted((w for w in candidates if w.key in met), key=lambda w: (last_seen.get(w.key, _NEVER), w.order))
    taken: set[str] = set()
    fresh = _distinct(new, taken)[:NEW_WORDS if len(review) >= size - NEW_WORDS else NEW_WORDS_FIRST]
    known = _distinct(review, taken)[:max(size - len(fresh), 0)]
    words = [*fresh, *known]
    odd = _odd_one_out(pool, words, met, rng) if size >= ODD_ONE_OUT_MIN_SIZE else None
    if odd is not None and len(words) >= size and known:  # it takes the place of one word met before
        known = known[:-1]
        words = [*fresh, *known]
    used: dict[str, set[tuple[str, str]]] = {word.id: set() for word in words}
    sentences: set[str] = set()
    first: list[Draft] = []
    for word in fresh:  # recognition first
        draft = generators.word_choice(pool, word, rng, "meaning")
        if draft is not None:
            used[word.id].add(("choice", "meaning"))
            first.append(draft)
    for word in known:
        draft = _item(pool, word, rng, used=used[word.id], sentences=sentences)
        if draft is not None:
            first.append(draft)
    rng.shuffle(first)
    more: list[Draft] = []
    room = size - len(first) - (odd is not None)
    while room > 0:
        added = False
        for word in words:
            if room <= 0:
                break
            draft = _item(pool, word, rng, used=used[word.id], sentences=sentences)
            if draft is not None:
                more.append(draft)
                room -= 1
                added = True
        if not added:
            break
    rng.shuffle(more)
    if odd is not None:
        more.insert(rng.randrange(len(more) + 1), odd)
    graded = _spread([*first, *more])[:size]
    for draft in graded:
        draft.key["met"] = sorted({key for key in draft.key.get("words", {}).values() if key in met})
    return [generators.intro(pool.stage_id, fresh), *graded] if fresh else graded
