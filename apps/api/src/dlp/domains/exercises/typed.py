"""Items answered by typing (typed cloze, typed recall) or by saying whether a word was known (flashcard).

Typed answers are judged by compare.py: a missing accent, or an article the item forgives, is correct with a
note; "almost" (a slip of the keyboard, a wrong de/het where the article is optional) closes the item in a
neutral colour and is never a mistake. A word copied from the cue is another word, never a slip. The prompt
carries a hint (first letter, letters per word) that the screen shows only when the learner asks; using it is
reported with the answer. A typed answer the check refuses may be overruled by the learner ("mijn antwoord
klopt ook"), which never counts towards completing anything.
"""
from __future__ import annotations

from typing import Any

from dlp.domains.curriculum.library import normalise
from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.generators import Draft, word_card
from dlp.domains.exercises.pool import Pool, Word, gives_away


def _hint(answer: str) -> dict[str, Any]:
    """The first letter and the letters of each word: "tot ziens" is 3 and 5, "e-mail" is 5 (a space, hyphen or
    apostrophe is not a letter)."""
    return {"first": answer[0], "letters": [sum(char.isalpha() for char in word) for word in answer.split()]}


def _refs(word: Word) -> dict[str, dict[str, str]]:
    return {"words": {"answer": word.key}, "refs": {"answer": f"word:{word.id}"}}


def _cue_words(cue: dict[str, str]) -> list[str]:
    """The words of the cue: typed back, they are other words, not slips of the answer ("milk" for "melk")."""
    return sorted({token for text in cue.values() for token in fold(text).split()})


def _same_meaning(word: Word, other: Word) -> bool:
    """Another term the cue fits as well: the same gloss in every language the cue shows, the same word class."""
    return (other.id != word.id and bool(other.article) == bool(word.article)
            and all(normalise(other.meaning[lang]) == normalise(word.meaning[lang]) for lang in ("en", "fa")))


def cloze_typed(pool: Pool, word: Word) -> Draft | None:
    """The word's example with the word blanked, its translation as the cue, the word to be typed as it stands
    in the sentence."""
    if word.span is None or gives_away(word):
        return None
    start, end = word.span
    surface = word.example["nl"][start:end]
    cue = {"en": word.example["en"], "fa": word.example["fa"]}
    return Draft(kind="cloze_typed", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "cloze_typed", "sentence": word.example["nl"][:start] + "___" + word.example["nl"][end:],
                         "cue": cue, "hint": _hint(surface)},
                 key={"accepted": [surface], "article": "none", "cue_words": _cue_words(cue),
                      "word": word_card(word), "sentence": word.example["nl"], **_refs(word)})


def typed_recall(pool: Pool, word: Word) -> Draft | None:
    """The meaning in the support language; the Dutch word to be typed. Another word of the stage with the same
    meaning is right too; a missing article is forgiven and noted. Not for a word its meaning spells ("bed")."""
    if gives_away(word, word.meaning):
        return None
    accepted = [word.term, *(other.term for other in pool.words if _same_meaning(word, other))]
    cue = {"en": word.meaning["en"], "fa": word.meaning["fa"]}
    return Draft(kind="typed_recall", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "typed_recall", "cue": cue, "hint": _hint(word.core)},
                 key={"accepted": accepted, "article": "optional" if word.article else "none",
                      "cue_words": _cue_words(cue), "word": word_card(word), **_refs(word)})


def flashcard(word: Word) -> Draft:
    """The Dutch word; the learner turns the card and says whether they knew it. Self-assessed, so it never
    writes a mistake."""
    return Draft(kind="flashcard", ref=f"word:{word.id}", word=word.key, words=(word.id,),
                 prompt={"kind": "flashcard", "term": word.term},
                 key={"word": word_card(word), **_refs(word)})
