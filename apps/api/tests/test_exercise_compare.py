"""The specification of tolerant comparison: what is forgiven, what is "almost", what is wrong."""
from __future__ import annotations

import pytest

from dlp.domains.exercises.compare import DiffOp, compare, distance, fold, is_slip

LEXICON = frozenset({"kaas", "kast", "bed", "bad", "huis"})


@pytest.mark.parametrize(("given", "expected", "outcome", "notes"), [
    # case, punctuation and spaces never matter
    ("ik woon in gent", "Ik woon in Gent.", "correct", ()),
    ("  Ik   woon in Gent!! ", "Ik woon in Gent.", "correct", ()),
    ("Hoe gaat het", "Hoe gaat het?", "correct", ()),
    # accents are forgiven and noted
    ("cafe", "café", "correct", ("accents",)),
    ("Een kop koffie", "Eén kop koffie", "correct", ("accents",)),
    # articles: a missing one is forgiven by default, a wrong one is almost, an extra one is noted
    ("appel", "de appel", "correct", ("article_missing",)),
    ("het appel", "de appel", "almost", ("article",)),
    ("een huis", "het huis", "almost", ("article",)),
    ("de appel", "appel", "correct", ("article_extra",)),
    # one slip in a word of four letters or more is almost; two from eight letters
    ("appl", "appel", "almost", ("spelling",)),
    ("apepl", "appel", "almost", ("spelling",)),
    ("fietsenwinkl", "fietsenwinkel", "almost", ("spelling",)),
    ("fitsenwinkl", "fietsenwinkel", "almost", ("spelling",)),
    ("fts", "fiets", "incorrect", ()),
    # short words have no slack
    ("dak", "dag", "incorrect", ()),
    # a slip that spells another known word is that word, not a slip
    ("kast", "kaas", "incorrect", ()),
    # a different form of the verb is not a slip
    ("ik wonen in gent", "Ik woon in Gent.", "incorrect", ()),
    # one missing or extra word in a longer sentence is almost; in a short one it is wrong
    ("ik woon gent", "Ik woon in Gent.", "almost", ("missing_word",)),
    ("ik woon wel in gent", "Ik woon in Gent.", "almost", ("extra_word",)),
    ("woon gent", "Ik woon in Gent.", "incorrect", ()),
    ("gent", "in Gent", "incorrect", ()),
    # nothing typed is not an answer
    ("", "fiets", "incorrect", ()),
    ("   ", "fiets", "incorrect", ()),
])
def test_comparison_table(given, expected, outcome, notes):
    result = compare(given, expected, lexicon=LEXICON)
    assert (result.outcome, result.notes) == (outcome, notes), result


def test_a_required_article_makes_a_bare_noun_almost():
    result = compare("appel", "de appel", article="required")
    assert (result.outcome, result.notes) == ("almost", ("article_missing",))


def test_the_kindest_accepted_answer_wins():
    result = compare("ik ben moe", ["Ik voel me moe.", "Ik ben moe."])
    assert result.outcome == "correct" and result.expected == "Ik ben moe."
    almost = compare("ik ben mooe", ["Ik voel me moe.", "Ik ben moe."])
    assert almost.outcome == "incorrect", "moe has three letters: no slack"
    with pytest.raises(ValueError):
        compare("ja", [])


def test_the_diff_says_what_is_missing_extra_or_changed():
    result = compare("ik woonn graag gent", "Ik woon in Gent.")
    assert result.diff == (
        DiffOp("same", "ik", "ik"),
        DiffOp("changed", "woon", "woonn"),
        DiffOp("changed", "in", "graag"),
        DiffOp("same", "gent", "gent"),
    )
    assert compare("ik woon gent", "Ik woon in Gent.").diff == (
        DiffOp("same", "ik", "ik"),
        DiffOp("same", "woon", "woon"),
        DiffOp("missing", "in"),
        DiffOp("same", "gent", "gent"),
    )


def test_the_building_blocks():
    assert fold("  ’s Morgens, “Goedemorgen!” ") == "'s morgens goedemorgen"
    assert distance("appel", "apepl") == 1, "two neighbours swapped is one slip"
    assert distance("kitten", "sitting") == 3
    assert is_slip("appel", "appl") and not is_slip("appel", "appel")
    assert not is_slip("kaas", "kast", LEXICON)
