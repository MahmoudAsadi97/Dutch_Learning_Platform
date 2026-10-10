"""The one list of mistake categories (roadmap shared contract "Mistakes").

Exercise items, writing corrections, conversation feedback and the tutor all name a mistake with one of these
categories; `learner_mistakes.taxonomy_version` records which rule set derived it, so a later change of the
rules does not silently re-label old rows. The tutor's authored notes (P6) are validated against this list.
"""
from __future__ import annotations

from typing import Literal

TAXONOMY_VERSION = "t1"

Category = Literal[
    "vocabulary_meaning", "vocabulary_form", "article", "spelling", "word_order", "grammar_form", "missing_word",
    "listening_discrimination", "comprehension", "punctuation", "word_choice", "preposition",
]
CATEGORIES: tuple[str, ...] = Category.__args__  # type: ignore[attr-defined]

# what a missed item of each kind says about the learner's Dutch
KIND_CATEGORY: dict[str, Category] = {
    "choice": "vocabulary_meaning",
    "cloze_choice": "word_choice",
    "odd_one_out": "vocabulary_meaning",
}


def category_for(kind: str, *, authored: bool = False) -> Category:
    """An authored comprehension question tests understanding of its text, not one word."""
    return "comprehension" if authored else KIND_CATEGORY[kind]
