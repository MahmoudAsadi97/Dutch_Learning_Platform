"""Items answered by typing (typed cloze, typed recall) or by saying whether a word was known (flashcard).

Typed answers are judged by compare.py: "almost" (an accent, a slip, a missing article where the item allows
it) closes the item in a neutral colour and is never a mistake. The prompt carries a hint (first letter and
length) that the screen shows only when the learner asks; using it is reported with the answer. A typed
answer that the check refuses may be overruled by the learner ("mijn antwoord klopt ook"), which never
counts towards completing anything.
"""
from __future__ import annotations

from typing import Any

from dlp.domains.exercises.generators import Draft, word_card
from dlp.domains.exercises.pool import Pool, Word, gives_away


def _hint(answer: str) -> dict[str, Any]:
    return {"first": answer[0], "length": len(answer)}


def _refs(word: Word) -> dict[str, dict[str, str]]:
    return {"words": {"answer": word.key}, "refs": {"answer": f"word:{word.id}"}}


def cloze_typed(pool: Pool, word: Word) -> Draft | None:
    """The word's example with the word blanked, its translation as the cue, the word to be typed as it stands
    in the sentence."""
    if word.span is None or gives_away(word):
        return None
    start, end = word.span
    surface = word.example["nl"][start:end]
    return Draft(kind="cloze_typed", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "cloze_typed", "sentence": word.example["nl"][:start] + "___" + word.example["nl"][end:],
                         "cue": {"en": word.example["en"], "fa": word.example["fa"]}, "hint": _hint(surface)},
                 key={"accepted": [surface], "article": "none", "word": word_card(word),
                      "sentence": word.example["nl"], **_refs(word)})


def typed_recall(pool: Pool, word: Word) -> Draft:
    """The meaning in the support language; the Dutch word to be typed. Another word of the stage with the same
    meaning is right too; a missing article is forgiven and noted."""
    accepted = [word.term, *(other.term for other in pool.words if other.id != word.id and other.senses & word.senses)]
    return Draft(kind="typed_recall", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "typed_recall", "cue": {"en": word.meaning["en"], "fa": word.meaning["fa"]},
                         "hint": _hint(word.core)},
                 key={"accepted": accepted, "article": "optional" if word.article else "none",
                      "word": word_card(word), **_refs(word)})


def flashcard(word: Word) -> Draft:
    """The Dutch word; the learner turns the card and says whether they knew it. Self-assessed, so it never
    writes a mistake."""
    return Draft(kind="flashcard", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "flashcard", "term": word.term},
                 key={"word": word_card(word), **_refs(word)})
