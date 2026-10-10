"""Grading an answer against an item's key, on the server only.

Option kinds compare the chosen option id with the key. Typed kinds (step 3.4) go through compare.py, whose
"almost" never counts as a mistake.
"""
from __future__ import annotations

from typing import Any, Literal

OPTION_KINDS = frozenset({"choice", "cloze_choice", "odd_one_out"})


def grade(kind: str, key: dict[str, Any], option: str) -> Literal["correct", "incorrect"]:
    if kind not in OPTION_KINDS:
        raise ValueError(f"{kind} is not graded by option")
    return "correct" if option == key["answer"] else "incorrect"
