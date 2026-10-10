"""Compare what a learner typed with what was expected, the way a patient teacher would.

Case, punctuation, quotation marks and spacing never matter. Missing accents, apostrophes and hyphens are
forgiven and noted ("cafe", "s morgens", "email"). A single term may carry an article policy: a missing
article is forgiven ("optional") or "almost" ("required"), and a wrong one is "almost": the word is right, de
or het is not. Sentences have no article policy; their first word is compared like any other. One slip of the
keyboard in a long enough word is "almost", unless the slip spells another real word the learner may have
meant ("bed" for "bad"), touches a negation (geen/een, niet/net) or a number. A compound typed as two words,
or two words typed as one, is a slip. In a sentence of four words or more one missing or extra function word
("in", "wel") is "almost"; a missing content word or negation is not. "Almost" is shown in a neutral colour
and never counts as a mistake.

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
# "none" for sentences; a term item (article + noun) chooses "optional" or "required"
ArticlePolicy = Literal["none", "optional", "required"]

ARTICLES = frozenset({"de", "het", "een"})
# a slip that turns one of these into another word reverses the meaning; never forgiven
NEGATIONS = frozenset({"niet", "geen", "nooit", "niets", "niks", "niemand", "nergens"})
# the only words a longer sentence may miss or add and still be "almost"
FUNCTION_WORDS = ARTICLES | frozenset({
    "in", "op", "aan", "naar", "van", "met", "voor", "bij", "uit", "om", "over", "tot", "te", "door", "tegen",
    "onder", "achter", "naast", "tussen", "sinds", "zonder", "er", "wel", "ook", "toch", "maar", "even", "eens",
    "hoor", "nou",
})
# elided words that keep their apostrophe at the edge
ELISIONS = frozenset({"'s", "'t", "'n", "'k", "'m"})
# one slip (a letter added, dropped, changed, or two neighbours swapped) is forgiven from this word length
NEAR_MISS_MIN_LENGTH = 4
# from this length two slips are
TWO_SLIPS_MIN_LENGTH = 8
# a sentence this long may miss or add one function word and still be "almost"
WORD_SLIP_MIN_TOKENS = 4
# changed stretches longer than this (expected words times typed words) are paired by position
MAX_PAIRING = 400

_RANK = {"correct": 0, "almost": 1, "incorrect": 2}
_NOT_TEXT = re.compile(r"[^\w\s'-]", re.UNICODE)
# the acute accent and other marks people type for an apostrophe; NFKC would split a word on ´
_APOSTROPHES = str.maketrans({"´": "'", "`": "'", "ʼ": "'", "′": "'", "’": "'", "‘": "'"})


@dataclass(frozen=True)
class DiffOp:
    op: Literal["same", "missing", "extra", "changed"]
    expected: str = ""
    given: str = ""


@dataclass(frozen=True)
class Comparison:
    outcome: Outcome
    # what was forgiven or what made it "almost": accents, punctuation, article_missing, article_extra, article,
    # spelling, missing_word, extra_word
    notes: tuple[str, ...]
    expected: str  # the accepted answer it was compared with
    diff: tuple[DiffOp, ...]


def fold(text: str) -> str:
    """Lower case, plain apostrophes, no punctuation or quotation marks, single spaces; accents are kept."""
    text = unicodedata.normalize("NFKC", text.translate(_APOSTROPHES)).casefold()
    words = (word if word in ELISIONS else word.strip("'-") for word in _NOT_TEXT.sub(" ", text).split())
    return " ".join(word for word in words if word)


def strip_accents(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))


def _bare(token: str) -> str:
    return token.replace("'", "").replace("-", "")


def _plain(token: str) -> str:
    """What two tokens are compared on: no accents, apostrophes or hyphens."""
    return strip_accents(_bare(token))


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
    """A keyboard slip, not another word: close enough for the word's length, and not itself a known word, a
    negation or a number."""
    if given in lexicon or {expected, given} & NEGATIONS or any(char.isdigit() for char in expected + given):
        return False
    allowed = 2 if len(expected) >= TWO_SLIPS_MIN_LENGTH else 1 if len(expected) >= NEAR_MISS_MIN_LENGTH else 0
    if abs(len(expected) - len(given)) > allowed:
        return False
    return 0 < distance(expected, given) <= allowed


def _split_article(tokens: list[str]) -> tuple[str | None, list[str]]:
    # "één" is the numeral, never an article
    if len(tokens) > 1 and tokens[0] in ARTICLES:
        return tokens[0], tokens[1:]
    return None, tokens


def _pair(expected: list[str], given: list[str]) -> list[DiffOp]:
    """One changed stretch of a diff. A word split in two or two words run together is one change; otherwise
    each word is paired with its closest counterpart, in order, and the rest is missing or extra."""
    plain_expected, plain_given = [_plain(token) for token in expected], [_plain(token) for token in given]
    if min(len(expected), len(given)) == 1 < max(len(expected), len(given)):
        joined_expected, joined_given = "".join(plain_expected), "".join(plain_given)
        if joined_expected == joined_given or is_slip(joined_expected, joined_given):
            return [DiffOp("changed", " ".join(expected), " ".join(given))]
    m, n = len(expected), len(given)
    if m * n > MAX_PAIRING:
        paired = min(m, n)
        return ([DiffOp("changed", expected[k], given[k]) for k in range(paired)]
                + [DiffOp("missing", word) for word in expected[paired:]]
                + [DiffOp("extra", given=word) for word in given[paired:]])
    # cost[i][j]: the cheapest alignment of expected[:i] with given[:j]; leaving a word out costs its length
    cost = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        cost[i][0] = cost[i - 1][0] + max(len(plain_expected[i - 1]), 1)
    for j in range(1, n + 1):
        cost[0][j] = cost[0][j - 1] + max(len(plain_given[j - 1]), 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost[i][j] = min(cost[i - 1][j - 1] + distance(plain_expected[i - 1], plain_given[j - 1]),
                             cost[i - 1][j] + max(len(plain_expected[i - 1]), 1),
                             cost[i][j - 1] + max(len(plain_given[j - 1]), 1))
    ops: list[DiffOp] = []
    i, j = m, n
    while i or j:
        if i and j and cost[i][j] == cost[i - 1][j - 1] + distance(plain_expected[i - 1], plain_given[j - 1]):
            ops.append(DiffOp("changed", expected[i - 1], given[j - 1]))
            i, j = i - 1, j - 1
        elif i and cost[i][j] == cost[i - 1][j] + max(len(plain_expected[i - 1]), 1):
            ops.append(DiffOp("missing", expected[i - 1]))
            i -= 1
        else:
            ops.append(DiffOp("extra", given=given[j - 1]))
            j -= 1
    return ops[::-1]


def _diff(expected: list[str], given: list[str]) -> list[DiffOp]:
    plain_expected = [_plain(token) for token in expected]
    plain_given = [_plain(token) for token in given]
    ops: list[DiffOp] = []
    for tag, e1, e2, g1, g2 in SequenceMatcher(a=plain_expected, b=plain_given, autojunk=False).get_opcodes():
        if tag == "equal":
            ops += [DiffOp("same", expected[i], given[j]) for i, j in zip(range(e1, e2), range(g1, g2), strict=True)]
        else:
            ops += _pair(expected[e1:e2], given[g1:g2])
    return ops


def _slip(op: DiffOp, lexicon: frozenset[str]) -> bool:
    expected, given = _plain(op.expected), _plain(op.given)
    if " " in expected or " " in given:  # a compound typed as two words, or two words typed as one
        expected, given = expected.replace(" ", ""), given.replace(" ", "")
        return expected == given or is_slip(expected, given)
    return is_slip(expected, given, lexicon)


def _compare_one(given: str, expected: str, article: ArticlePolicy, lexicon: frozenset[str]) -> Comparison:
    expected_tokens, given_tokens = fold(expected).split(), fold(given).split()
    if not given_tokens:
        return Comparison("incorrect", (), expected, tuple(_diff(expected_tokens, [])))
    notes: list[str] = []
    almost = False
    expected_core, given_core = expected_tokens, given_tokens
    if article != "none":
        expected_article, expected_core = _split_article(expected_tokens)
        given_article, given_core = _split_article(given_tokens)
        lone_article = given_tokens[0] in ARTICLES and len(given_tokens) == 1
        if expected_article and not given_article and not lone_article:
            notes.append("article_missing")
            almost = article == "required"
        elif given_article and not expected_article:
            notes.append("article_extra")
        elif expected_article and given_article and expected_article != given_article:
            notes.append("article")
            almost = True
    ops = _diff(expected_core, given_core)
    same = [op for op in ops if op.op == "same"]
    if any(_bare(op.expected) != _bare(op.given) for op in same):
        notes.append("accents")
    if any(strip_accents(op.expected) != strip_accents(op.given) for op in same):
        notes.append("punctuation")
    changed = [op for op in ops if op.op == "changed"]
    loose = [op for op in ops if op.op in ("missing", "extra")]
    diff = tuple(_diff(expected_tokens, given_tokens))
    if not (changed or loose):
        return Comparison("almost" if almost else "correct", tuple(notes), expected, diff)
    slips = all(_slip(op, lexicon) for op in changed)
    word_slip = (len(loose) == 1 and not changed and len(expected_core) >= WORD_SLIP_MIN_TOKENS
                 and _bare(loose[0].expected or loose[0].given) in FUNCTION_WORDS)
    if slips and (not loose or word_slip):
        notes += (["spelling"] * bool(changed) + ["missing_word"] * any(op.op == "missing" for op in loose)
                  + ["extra_word"] * any(op.op == "extra" for op in loose))
        return Comparison("almost", tuple(notes), expected, diff)
    return Comparison("incorrect", tuple(notes), expected, diff)


def _lexicon(words: frozenset[str]) -> frozenset[str]:
    """Library terms compared the way a typed word is: without their article, accents or apostrophes, word by
    word ("de broek" -> broek, "geëerd" -> geeerd)."""
    return frozenset(_plain(token) for word in words for token in _split_article(fold(word).split())[1])


def compare(given: str, accepted: str | Sequence[str], *, article: ArticlePolicy = "none",
            lexicon: frozenset[str] = frozenset()) -> Comparison:
    """The kindest reading of `given` against any accepted answer: correct before almost before incorrect,
    then the fewest notes, then the closest."""
    answers = [accepted] if isinstance(accepted, str) else list(accepted)
    if not answers:
        raise ValueError("an exercise needs at least one accepted answer")
    if len(given) > 2 * max(len(answer) for answer in answers) + 64:  # not an attempt at this answer
        return Comparison("incorrect", (), answers[0], ())
    words = _lexicon(lexicon)
    results = [_compare_one(given, answer, article, words) for answer in answers]
    return min(results, key=lambda result: (_RANK[result.outcome], len(result.notes),
                                            sum(op.op != "same" for op in result.diff)))
