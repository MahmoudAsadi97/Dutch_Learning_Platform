"""Which words a session practises, with which items, in which order.

A session takes up to NEW_WORDS new words (never practised in an earlier session and not in the word bank)
in library order, and fills the rest with words met before, the least recently practised first; a first
session, with nothing to review yet, introduces up to NEW_WORDS_FIRST. New words are shown on an ungraded
intro card first and first practised by recognition (the Dutch word to its meaning). Every word gets one
item, and further items in another kind or direction until the session has its size. No two cloze items use
the same example (one example serves several A1 words; from pre-B2 an example also holds the next word's
sentence), and no cloze target stands in another cloze's sentence. No two items about the same word follow
each other where another order allows it, and one odd-one-out item joins where the stage has it and three
words of one situation and word class are known.
"""
from __future__ import annotations

import random
from collections import Counter
from datetime import UTC, datetime

from dlp.domains.exercises import generators
from dlp.domains.exercises.generators import Draft
from dlp.domains.exercises.pool import Pool, Word, word_pattern

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


def _cloze_fits(word: Word, clozes: list[Word]) -> bool:
    """A cloze on `word` repeats no example or sentence frame and shows no other cloze's answer, nor is its
    answer shown."""
    return all(word.example["nl"] != other.example["nl"] and word.frame != other.frame
               and not word_pattern(word.core).search(other.example["nl"])
               and not word_pattern(other.core).search(word.example["nl"]) for other in clozes)


def _item(pool: Pool, word: Word, rng: random.Random, *, used: set[tuple[str, str]],
          clozes: list[Word]) -> Draft | None:
    """An item for `word` in a kind or direction it has not had in this session."""
    options: list[tuple[str, str]] = [("choice", direction) for direction in generators.directions(pool)]
    card = pool.cloze.get(word.id)
    if card and _cloze_fits(word, clozes):
        options.append(("cloze_choice", ""))
    rng.shuffle(options)
    for kind, direction in options:
        if (kind, direction) in used:
            continue
        draft = (generators.cloze_choice(pool, word, rng) if kind == "cloze_choice"
                 else generators.word_choice(pool, word, rng, direction))
        if draft is not None:
            used.add((kind, direction))
            if kind == "cloze_choice":
                clozes.append(word)
            return draft
    return None


def _odd_one_out(pool: Pool, words: list[Word], met: frozenset[str], rng: random.Random) -> Draft | None:
    if not pool.odd_one_out:
        return None
    for topic in dict.fromkeys(word.topic for word in words):
        for noun in (True, False):
            group = [w for w in words if w.topic == topic and bool(w.article) == noun]
            group += [w for w in pool.by_topic[topic] if w.key in met and bool(w.article) == noun and w not in group]
            if len(group) >= 3:
                draft = generators.odd_one_out(pool, group[:3], rng)
                if draft is not None:
                    return draft
    return None


def _spread(drafts: list[Draft]) -> list[Draft]:
    """No two items about the same word in a row, where another order allows it. Keeps the given order as far as
    possible and the order of each word's own items (recognition first)."""
    remaining = list(drafts)
    placed: list[Draft] = []
    while remaining:
        last = placed[-1].word if placed else ""
        counts = Counter(draft.word for draft in remaining if draft.word)
        crowded = [word for word, count in counts.items() if word != last and count * 2 > len(remaining)]
        choice = next((d for d in remaining if d.word in crowded), None) if crowded else None
        if choice is None:
            choice = next((d for d in remaining if not d.word or d.word != last), remaining[0])
        remaining.remove(choice)
        placed.append(choice)
    return placed


def plan(pool: Pool, rng: random.Random, *, size: int, met: frozenset[str],
         last_seen: dict[str, datetime] | None = None, library_topic: str | None = None) -> list[Draft]:
    """The session's drafts in order: the intro card (when there are new words), then the graded items."""
    last_seen = last_seen or {}
    candidates = [w for w in (pool.by_topic[library_topic] if library_topic else pool.words) if w.id in pool.choice]
    new = [w for w in candidates if w.key not in met]
    review = sorted((w for w in candidates if w.key in met), key=lambda w: (last_seen.get(w.key, _NEVER), w.order))
    taken: set[str] = set()
    fresh = _distinct(new, taken)[:min(NEW_WORDS if len(review) >= size - NEW_WORDS else NEW_WORDS_FIRST, size)]
    known = _distinct(review, taken)[:max(size - len(fresh), 0)]
    words = [*fresh, *known]
    odd = _odd_one_out(pool, words, met, rng) if size >= ODD_ONE_OUT_MIN_SIZE else None
    if odd is not None and len(words) >= size:  # it takes the place of a word met before, or of a new one
        if known:
            known = known[:-1]
        else:
            fresh = fresh[:-1]
        words = [*fresh, *known]
    used: dict[str, set[tuple[str, str]]] = {word.id: set() for word in words}
    clozes: list[Word] = []
    first: list[Draft] = []
    for word in fresh:  # recognition first
        draft = generators.word_choice(pool, word, rng, "meaning")
        if draft is not None:
            used[word.id].add(("choice", "meaning"))
            first.append(draft)
    for word in known:
        draft = _item(pool, word, rng, used=used[word.id], clozes=clozes)
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
            draft = _item(pool, word, rng, used=used[word.id], clozes=clozes)
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
    # the intro card shows only the new words the session goes on to practise
    practised = {draft.ref for draft in graded}
    shown = [word for word in fresh if f"word:{word.id}" in practised]
    return [generators.intro(pool.stage_id, shown), *graded] if shown else graded
