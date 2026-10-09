"""Compare what a learner typed with what was expected, the way a patient teacher would.

Case and punctuation never matter. Missing accents are forgiven and noted ("café"). A missing article is
forgiven when the exercise allows it; a wrong one makes the answer "almost": the word is right, de or het is
not. One slip of the keyboard in a long enough word is "almost", unless the slip spells another real word the
learner may have meant ("bed" for "bad"). In a longer sentence one missing or extra word is "almost" too.
"Almost" is shown in a neutral colour and never counts as a mistake.

Pure: no database, no model. The thresholds are named constants; tests/test_exercise_compare.py is their
specification.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

Outcome = Literal["correct", "almost", "incorrect"]
ArticlePolicy = Literal["optional", "required"]

ARTICLES = frozenset({"de", "het", "een"})
# one slip (a letter added, dropped, changed, or two neighbours swapped) is forgiven from this word length
NEAR_MISS_MIN_LENGTH = 4
# from this length two slips are
TWO_SLIPS_MIN_LENGTH = 8
# a sentence this long may miss or add one word and still be "almost"
WORD_SLIP_MIN_TOKENS = 4

_RANK = {"correct": 0, "almost": 1, "incorrect": 2}
_NOT_TEXT = re.compile(r"[^\w\s'-]", re.UNICODE)


@dataclass(frozen=True)
class DiffOp:
    op: Literal["same", "missing", "extra", "changed"]
    expected: str = ""
    given: str = ""


@dataclass(frozen=True)
class Comparison:
    outcome: Outcome
    # what was forgiven or what made it "almost": accents, article_missing, article_extra, article, spelling,
    # missing_word, extra_word
    notes: tuple[str, ...]
    expected: str  # the accepted answer it was compared with
    diff: tuple[DiffOp, ...]


def fold(text: str) -> str:
    """Lower case, plain quotes, no punctuation, single spaces; accents are kept."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("’", "'").replace("‘", "'")
    return " ".join(_NOT_TEXT.sub(" ", text).split())


def strip_accents(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))


def distance(a: str, b: str) -> int:
    """Edits between two words: insert, delete, substitute, or swap two neighbours (optimal string alignment)."""
    rows = [list(range(len(b) + 1))]
    for i in range(1, len(a) + 1):
        row = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            row[j] = min(rows[i - 1][j] + 1, row[j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                row[j] = min(row[j], rows[i - 2][j - 2] + 1)
        rows.append(row)
    return rows[-1][-1]


def is_slip(expected: str, given: str, lexicon: frozenset[str] = frozenset()) -> bool:
    """A keyboard slip, not another word: close enough for the word's length, and not itself a known word."""
    if given in lexicon:
        return False
    allowed = 2 if len(expected) >= TWO_SLIPS_MIN_LENGTH else 1 if len(expected) >= NEAR_MISS_MIN_LENGTH else 0
    return 0 < distance(expected, given) <= allowed


def _split_article(tokens: list[str]) -> tuple[str | None, list[str]]:
    if len(tokens) > 1 and strip_accents(tokens[0]) in ARTICLES:
        return tokens[0], tokens[1:]
    return None, tokens


def _diff(expected: list[str], given: list[str]) -> list[DiffOp]:
    plain_expected = [strip_accents(token) for token in expected]
    plain_given = [strip_accents(token) for token in given]
    ops: list[DiffOp] = []
    for tag, e1, e2, g1, g2 in SequenceMatcher(a=plain_expected, b=plain_given, autojunk=False).get_opcodes():
        if tag == "equal":
            ops += [DiffOp("same", expected[i], given[j]) for i, j in zip(range(e1, e2), range(g1, g2), strict=True)]
            continue
        paired = min(e2 - e1, g2 - g1) if tag == "replace" else 0
        ops += [DiffOp("changed", expected[e1 + k], given[g1 + k]) for k in range(paired)]
        ops += [DiffOp("missing", expected[i]) for i in range(e1 + paired, e2)]
        ops += [DiffOp("extra", given=given[j]) for j in range(g1 + paired, g2)]
    return ops


def _compare_one(given: str, expected: str, article: ArticlePolicy, lexicon: frozenset[str]) -> Comparison:
    expected_tokens, given_tokens = fold(expected).split(), fold(given).split()
    notes: list[str] = []
    almost = False
    expected_article, expected_core = _split_article(expected_tokens)
    given_article, given_core = _split_article(given_tokens)
    if expected_article and not given_article:
        notes.append("article_missing")
        almost = article == "required"
    elif given_article and not expected_article:
        notes.append("article_extra")
    elif expected_article and given_article and strip_accents(expected_article) != strip_accents(given_article):
        notes.append("article")
        almost = True
    ops = _diff(expected_core, given_core)
    # "een" for "Eén" is the right article without its accent, "cafe" for "café" the right word without one
    article_accents = bool(expected_article and given_article) and expected_article != given_article and not almost
    if article_accents or any(op.op == "same" and op.expected != op.given for op in ops):
        notes.append("accents")
    changed = [op for op in ops if op.op == "changed"]
    missing = [op for op in ops if op.op == "missing"]
    extra = [op for op in ops if op.op == "extra"]
    diff = tuple(_diff(expected_tokens, given_tokens))
    if not given_tokens:
        return Comparison("incorrect", (), expected, diff)
    if not (changed or missing or extra):
        return Comparison("almost" if almost else "correct", tuple(notes), expected, diff)
    slips = all(is_slip(strip_accents(op.expected), strip_accents(op.given), lexicon) for op in changed)
    word_slip = len(missing) + len(extra) <= 1 and len(expected_core) >= WORD_SLIP_MIN_TOKENS
    if slips and (not (missing or extra) or (word_slip and not changed)):
        notes += ["spelling"] * bool(changed) + ["missing_word"] * bool(missing) + ["extra_word"] * bool(extra)
        return Comparison("almost", tuple(notes), expected, diff)
    return Comparison("incorrect", tuple(notes), expected, diff)


def compare(given: str, accepted: str | Sequence[str], *, article: ArticlePolicy = "optional",
            lexicon: frozenset[str] = frozenset()) -> Comparison:
    """The kindest reading of `given` against any accepted answer: correct before almost before incorrect,
    and among equals the one with the fewest notes."""
    answers = [accepted] if isinstance(accepted, str) else list(accepted)
    if not answers:
        raise ValueError("an exercise needs at least one accepted answer")
    folded_lexicon = frozenset(fold(word) for word in lexicon)
    results = [_compare_one(given, answer, article, folded_lexicon) for answer in answers]
    return min(results, key=lambda result: (_RANK[result.outcome], len(result.notes)))
