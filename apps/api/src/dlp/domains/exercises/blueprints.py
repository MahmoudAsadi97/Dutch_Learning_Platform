"""Which words a session practises, with which items, in which order.

A session takes up to NEW_WORDS new words (never practised in an earlier session and not in the word bank)
in library order, and fills the rest with words met before, the least recently practised first; a first
session, with nothing to review yet, introduces up to NEW_WORDS_FIRST. New words are shown on an ungraded
intro card first and first practised by recognition (the Dutch word to its meaning). Every word gets one
item, and further items in another kind or direction until the session has its size: choice in its
directions, cloze by choice or typed, typed recall, the sentence builder, and with speech listen-and-choose,
dictation and shadowing (no typing or speaking in a tap-only while-you-wait session; no speech when the audio
allowance runs low). Items built on a word's example (cloze, typed cloze, sentence builder) never repeat an example or a
sentence frame (one example serves several A1 words; from pre-B2 an example also holds the next word's
sentence), and none shows another one's answer, nor does the paragraph of an ordering board. A dictated
sentence stands nowhere else in the session, not on the intro card nor on any item's word cards (one example
serves several A1 words, and every word card shows its example): such a dictation becomes another kind for the
same word. No two items about the same word follow each other where another order allows it.

Up to MAX_BOARDS boards take the place of single words: odd one out (where the stage has it and three words of
one situation and word class are known), match pairs on four of the session's words, de/het on six nouns the
learner knows or meets now (three of each, so "always de" scores half), and putting a Story Time paragraph
back in order (pre-B1 and from pre-B2), one that shares no sentence with the session's examples. Boards are
built from the words the session keeps, so every new word on a board is on the intro card. Flashcards are for
saved words without a meaning (word review, roadmap 5.1) and are not planned here.
"""
from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from dlp.domains.exercises import audio as spoken
from dlp.domains.exercises import boards, generators, typed
from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.generators import Draft
from dlp.domains.exercises.pool import Pool, Word, gives_away, word_pattern

SIZES = {"stage_skill": 8, "while_you_wait": 5}
SIZE_MIN, SIZE_MAX = 5, 12
NEW_WORDS = 4
NEW_WORDS_FIRST = 6
ODD_ONE_OUT_MIN_SIZE = 6
MAX_BOARDS = 2
# kinds built on the word's example sentence: one per example and frame in a session
EXAMPLE_KINDS = ("cloze_choice", "cloze_typed", "sentence_builder", "dictation", "shadow")
# dictation is the word alone at the first stage, a sentence after it
DICTATION_SINGLE_STAGE = "pre-a1"
_NEVER = datetime.min.replace(tzinfo=UTC)


def _distinct(words: list[Word], taken: set[str]) -> list[Word]:
    picked: list[Word] = []
    for word in words:
        if word.key not in taken:
            taken.add(word.key)
            picked.append(word)
    return picked


def _cloze_fits(word: Word, clozes: list[Word], shown: tuple[str, ...] = ()) -> bool:
    """An example item on `word` repeats no example or sentence frame already used, shows no other one's answer,
    and its own answer stands in no other shown text (an ordering board's paragraph)."""
    return (all(word.example["nl"] != other.example["nl"] and word.frame != other.frame
                and not word_pattern(word.core).search(other.example["nl"])
                and not word_pattern(other.core).search(word.example["nl"]) for other in clozes)
            and not any(word_pattern(word.core).search(text) for text in shown))


def _item(pool: Pool, word: Word, rng: random.Random, *, used: set[tuple[str, str]],
          clozes: list[Word], shown: tuple[str, ...] = (), typing: bool = True, audio: bool = False) -> Draft | None:
    """An item for `word` in a kind or direction it has not had in this session; choice is one kind among the
    others (its direction is drawn after it), so recognition does not crowd out typing and building."""
    directions = list(generators.directions(pool))
    rng.shuffle(directions)
    choice = next((("choice", d) for d in directions if ("choice", d) not in used), None)
    options: list[tuple[str, str]] = [choice] if choice else []
    if typing:
        options.append(("typed_recall", ""))
    if _cloze_fits(word, clozes, shown):
        if word.id in pool.cloze:
            options.append(("cloze_choice", ""))
        if typing and word.span and not gives_away(word):
            options.append(("cloze_typed", ""))
        if word.id in pool.pieces:
            options.append(("sentence_builder", ""))
        if audio and typing:
            options += [("dictation", ""), ("shadow", "")]
    if audio:
        options.append(("listen_choose", ""))
    rng.shuffle(options)
    for kind, direction in options:
        if (kind, direction) in used:
            continue
        if kind == "cloze_choice":
            draft = generators.cloze_choice(pool, word, rng)
        elif kind == "cloze_typed":
            draft = typed.cloze_typed(pool, word)
        elif kind == "typed_recall":
            draft = typed.typed_recall(pool, word)
        elif kind == "sentence_builder":
            draft = boards.sentence_builder(pool, word, rng)
        elif kind == "listen_choose":
            draft = spoken.listen_choose(pool, word, rng)
        elif kind == "dictation":
            draft = spoken.dictation(pool, word, single=pool.stage_id == DICTATION_SINGLE_STAGE)
        elif kind == "shadow":
            draft = spoken.shadow(pool, word)
        else:
            draft = generators.word_choice(pool, word, rng, direction)
        if draft is not None:
            used.add((kind, direction))
            if kind in EXAMPLE_KINDS:
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


def _match_pairs(pool: Pool, words: list[Word], rng: random.Random) -> Draft | None:
    order = list(words)
    rng.shuffle(order)
    picked: list[Word] = []
    for word in order:
        if all(word.key != other.key and word.core != other.core and not word.senses & other.senses
               for other in picked):
            picked.append(word)
        if len(picked) == boards.PAIRS:
            return boards.match_pairs(pool, picked, rng)
    return None


def _de_het(pool: Pool, words: list[Word], met: frozenset[str], rng: random.Random) -> Draft | None:
    sortable = set(pool.sortable)
    nouns = [w for w in words if w.id in sortable]
    nouns += [pool.by_id[i] for i in pool.sortable if pool.by_id[i].key in met and pool.by_id[i] not in nouns]
    half = boards.SORT_NOUNS // 2
    by_article = {article: [w for w in nouns if w.article == article] for article in ("de", "het")}
    if any(len(group) < half for group in by_article.values()):
        return None
    return boards.de_het(pool, [*rng.sample(by_article["de"], half), *rng.sample(by_article["het"], half)], rng)


def _sentence_order(pool: Pool, words: list[Word], rng: random.Random) -> Draft | None:
    """A paragraph none of whose sentences the session shows elsewhere (an example on the intro card, a cloze,
    a word card), so no other item gives its order away; one linked to a session word when there is one."""
    examples = fold(" ".join(word.example["nl"] for word in words))
    runs = [run for run in pool.orders if not any(fold(text) in examples for text in run.sentences)]
    ids = {word.id for word in words}
    linked = [run for run in runs if run.words & ids]
    return boards.sentence_order(rng.choice(linked or runs), rng) if runs else None


def _boards(pool: Pool, words: list[Word], met: frozenset[str], rng: random.Random, size: int) -> list[Draft]:
    """Up to MAX_BOARDS boards, chosen at random among those the words allow."""
    found = [board for board in (
        _odd_one_out(pool, words, met, rng) if size >= ODD_ONE_OUT_MIN_SIZE else None,
        _match_pairs(pool, words, rng),
        _de_het(pool, words, met, rng),
        _sentence_order(pool, words, rng),
    ) if board is not None]
    return rng.sample(found, min(MAX_BOARDS, len(found), max(size - 4, 0)))


def _targets(draft: Draft) -> set[str]:
    """The library words an item practises (a board: all of its words; odd one out and ordering: none)."""
    if draft.kind in ("match_pairs", "de_het"):
        return set(draft.words)
    if draft.ref.startswith("word:") and draft.kind != "odd_one_out":
        return {draft.ref.removeprefix("word:")}
    return set()


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


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for inner in value.values():
            yield from _strings(inner)
    elif isinstance(value, list | tuple):
        for inner in value:
            yield from _strings(inner)


def _shown_elsewhere(dictation: Draft, drafts: list[Draft]) -> bool:
    """Whether another draft (its prompt, or its key, which the feedback reveals) holds the dictated sentence."""
    text = fold(dictation.key["audio_text"])
    return any(text in fold(string) for draft in drafts if draft is not dictation
               for string in _strings((draft.prompt, draft.key)))


def plan(pool: Pool, rng: random.Random, *, size: int, met: frozenset[str],
         last_seen: dict[str, datetime] | None = None, library_topic: str | None = None,
         typing: bool = True, audio: bool = False) -> list[Draft]:
    """The session's drafts in order: the intro card (when there are new words), then the graded items.
    `typing` False leaves out the kinds answered by typing or speaking (a while-you-wait session is tapped
    only); `audio` adds the kinds with speech."""
    last_seen = last_seen or {}
    candidates = [w for w in (pool.by_topic[library_topic] if library_topic else pool.words) if w.id in pool.choice]
    new = [w for w in candidates if w.key not in met]
    review = sorted((w for w in candidates if w.key in met), key=lambda w: (last_seen.get(w.key, _NEVER), w.order))
    taken: set[str] = set()
    fresh = _distinct(new, taken)[:min(NEW_WORDS if len(review) >= size - NEW_WORDS else NEW_WORDS_FIRST, size)]
    known = _distinct(review, taken)[:max(size - len(fresh), 0)]
    words = [*fresh, *known]
    room_for = len(_boards(pool, words, met, random.Random(rng.random()), size))
    while room_for and len(words) + room_for > size:
        # a board takes the place of a new word beyond the usual number, else of a word met before
        if len(fresh) > NEW_WORDS or not known:
            fresh = fresh[:-1]
        else:
            known = known[:-1]
        words = [*fresh, *known]
    # the boards themselves come from the words the session keeps, so a new word on a board is introduced
    found = _boards(pool, words, met, rng, size)[:room_for]
    shown = tuple(text for board in found if board.kind == "sentence_order" for text in board.key["texts"])
    used: dict[str, set[tuple[str, str]]] = {word.id: set() for word in words}
    clozes: list[Word] = []
    first: list[Draft] = []
    for word in fresh:  # recognition first
        draft = generators.word_choice(pool, word, rng, "meaning")
        if draft is not None:
            used[word.id].add(("choice", "meaning"))
            first.append(draft)
    for word in known:
        draft = _item(pool, word, rng, used=used[word.id], clozes=clozes, shown=shown, typing=typing, audio=audio)
        if draft is not None:
            first.append(draft)
    rng.shuffle(first)
    more: list[Draft] = []
    room = size - len(first) - len(found)
    while room > 0:
        added = False
        for word in words:
            if room <= 0:
                break
            draft = _item(pool, word, rng, used=used[word.id], clozes=clozes, shown=shown, typing=typing,
                          audio=audio)
            if draft is not None:
                more.append(draft)
                room -= 1
                added = True
        if not added:
            break
    rng.shuffle(more)
    for board in found:
        more.insert(rng.randrange(len(more) + 1), board)
    graded = _spread([*first, *more])[:size]
    # the intro card shows the new words the session goes on to practise, and only those
    practised = set().union(*(_targets(draft) for draft in graded)) if graded else set()
    shown = [word for word in fresh if word.id in practised]
    intro = [generators.intro(pool.stage_id, shown)] if shown else []
    if pool.stage_id != DICTATION_SINGLE_STAGE:  # a dictated word alone is on its own choice options anyway
        for index, draft in reversed(list(enumerate(graded))):
            if draft.kind == "dictation" and _shown_elsewhere(draft, [*intro, *graded]):
                word = pool.by_id[draft.ref.removeprefix("word:")]
                other = _item(pool, word, rng, used=used[word.id], clozes=clozes, typing=typing, audio=audio)
                graded[index:index + 1] = [other] if other is not None else []
    for draft in graded:
        draft.key["met"] = sorted({key for key in draft.key.get("words", {}).values() if key in met})
    return [*intro, *graded]
