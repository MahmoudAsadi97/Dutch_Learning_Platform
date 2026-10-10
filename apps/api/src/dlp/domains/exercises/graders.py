"""Grading an answer against an item's key, on the server only.

Every grader returns the outcome, what the feedback may now show, and the parts the learner got wrong (an
option, a pair, a noun), so a board writes one mistake per missed word. Option kinds compare the chosen id
with the key. Typed kinds go through compare.py: a missing accent or a forgiven article is correct with a
note, a slip or a wrong de/het is "almost", which closes the item and is never a mistake; a word copied from
the cue is another word, not a slip. A board is judged part by part and is right when every part is. Putting
sentences back in order with one neighbouring pair swapped, or with the closing sentence moved to the front
(a general statement can open a paragraph as well as close it), is "almost". A flashcard is the learner's
own say; a built sentence may have another right order the check does not know: neither writes a mistake.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from dlp.domains.exercises.compare import compare, fold

OPTION_KINDS = frozenset({"choice", "cloze_choice", "odd_one_out", "listen_choose"})
TYPED_KINDS = frozenset({"cloze_typed", "typed_recall", "dictation"})
BOARD_KINDS = frozenset({"match_pairs", "de_het", "sentence_builder", "sentence_order"})
# kinds whose check may miss a right answer, so the learner may overrule it ("mijn antwoord klopt ook")
OVERRIDABLE = frozenset({"cloze_typed", "typed_recall", "dictation", "sentence_builder"})
# kinds whose misses are never mistakes: a learner's own say, a paragraph they may never have read, a sentence
# whose other right orders the check does not know, speech that was or was not heard (never a score)
NO_MISTAKES = frozenset({"flashcard", "sentence_order", "sentence_builder", "shadow"})

Outcome = Literal["correct", "almost", "incorrect"]


class InvalidAnswer(ValueError):
    """The answer does not fit the item (an unknown option, a board with pieces missing)."""


@dataclass
class Judgement:
    outcome: Outcome
    feedback: dict[str, Any] = field(default_factory=dict)
    misses: list[str] = field(default_factory=list)  # option ids, or "answer" for the whole item


def _ids(prompt: dict[str, Any], field_name: str) -> list[str]:
    return [entry["id"] for entry in prompt[field_name]]


def _whole(order: list[str] | None, ids: list[str]) -> list[str]:
    if order is None or sorted(order) != sorted(ids) or len(set(order)) != len(order):
        raise InvalidAnswer("put every piece in place, each once")
    return order


def grade(kind: str, prompt: dict[str, Any], key: dict[str, Any], answer: dict[str, Any],
          lexicon: frozenset[str] = frozenset()) -> Judgement:
    if kind in OPTION_KINDS:
        option = answer.get("option")
        if option not in _ids(prompt, "options"):
            raise InvalidAnswer("choose one of the item's options")
        right = option == key["answer"]
        return Judgement("correct" if right else "incorrect", {"given": option}, [] if right else [option])
    if kind in TYPED_KINDS:
        text = answer.get("text")
        if not isinstance(text, str) or not text.strip():
            raise InvalidAnswer("type an answer")
        result = compare(text, key["accepted"], article=key["article"],
                         lexicon=lexicon | frozenset(key.get("cue_words", ())))
        return Judgement(result.outcome, {"typed": text, "expected": result.expected, "notes": list(result.notes),
                                          "diff": [asdict(op) for op in result.diff]},
                         ["answer"] if result.outcome == "incorrect" else [])
    if kind == "flashcard":
        known = answer.get("known")
        if not isinstance(known, bool):
            raise InvalidAnswer("say whether you knew the word")
        return Judgement("correct" if known else "incorrect", {"known": known})
    if kind == "match_pairs":
        pairs = answer.get("pairs") or {}
        left, right = _ids(prompt, "left"), _ids(prompt, "right")
        if sorted(pairs) != sorted(left) or sorted(pairs.values()) != sorted(right):
            raise InvalidAnswer("match every word once")
        results = {i: {"given": pairs[i], "correct": key["pairs"][i], "ok": pairs[i] == key["pairs"][i]} for i in left}
        misses = [i for i, result in results.items() if not result["ok"]]
        return Judgement("incorrect" if misses else "correct", {"pairs": results}, misses)
    if kind == "de_het":
        bins = answer.get("bins") or {}
        ids = _ids(prompt, "options")
        if sorted(bins) != sorted(ids) or not set(bins.values()) <= {"de", "het"}:
            raise InvalidAnswer("sort every word")
        results = {i: {"given": bins[i], "correct": key["bins"][i], "ok": bins[i] == key["bins"][i]} for i in ids}
        misses = [i for i, result in results.items() if not result["ok"]]
        return Judgement("incorrect" if misses else "correct", {"bins": results}, misses)
    if kind == "sentence_builder":
        order = _whole(answer.get("order"), _ids(prompt, "tiles"))
        texts = dict(zip(key["order"], key["texts"], strict=True))
        given = [fold(texts[i]) for i in order]
        wanted = [fold(text) for text in key["texts"]]  # the same word twice may stand in either place
        first = next((n for n, (a, b) in enumerate(zip(given, wanted, strict=True)) if a != b), None)
        return Judgement("correct" if first is None else "incorrect",
                         {"order": key["order"], "given_order": order, "first_difference": first},
                         [] if first is None else ["answer"])
    if kind == "sentence_order":
        order = _whole(answer.get("order"), _ids(prompt, "sentences"))
        wanted = key["order"]
        wrong = [n for n, (a, b) in enumerate(zip(order, wanted, strict=True)) if a != b]
        swap = len(wrong) == 2 and wrong[1] == wrong[0] + 1 and order[wrong[0]] == wanted[wrong[1]]
        closing_first = order == [wanted[-1], *wanted[:-1]]
        outcome: Outcome = "correct" if not wrong else "almost" if swap or closing_first else "incorrect"
        return Judgement(outcome, {"order": wanted, "given_order": order, "translation": key.get("translation")},
                         ["answer"] if outcome == "incorrect" else [])
    raise ValueError(f"{kind} has no grader")
