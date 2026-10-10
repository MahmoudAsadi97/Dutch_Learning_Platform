"""The specification of tolerant comparison: what is forgiven, what is "almost", what is wrong."""
from __future__ import annotations

import pytest

from dlp.domains.exercises.compare import DiffOp, compare, distance, fold, is_slip

LEXICON = frozenset({"kaas", "kast", "bed", "bad", "huis"})


@pytest.mark.parametrize(("given", "expected", "outcome", "notes"), [
    # case, punctuation, quotation marks and spaces never matter
    ("ik woon in gent", "Ik woon in Gent.", "correct", ()),
    ("  Ik   woon in Gent!! ", "Ik woon in Gent.", "correct", ()),
    ("Hoe gaat het", "Hoe gaat het?", "correct", ()),
    ("Mijn buur zegt: Hallo, goeiemorgen!", "Mijn buur zegt: ‘Hallo, goeiemorgen!’", "correct", ()),
    ("ik ga - denk ik - morgen", "Ik ga, denk ik, morgen.", "correct", ()),
    ("auto´s", "auto's", "correct", ()),
    # accents, apostrophes and hyphens are forgiven and noted
    ("cafe", "café", "correct", ("accents",)),
    ("Een kop koffie", "Eén kop koffie", "correct", ("accents",)),
    ("s morgens", "'s morgens", "correct", ("punctuation",)),
    ("zn fiets", "z'n fiets", "correct", ("punctuation",)),
    ("email", "e-mail", "correct", ("punctuation",)),
    # a sentence has no article policy: its first word counts like any other
    ("spijt me", "Het spijt me.", "incorrect", ()),
    ("keer per week", "Eén keer per week.", "incorrect", ()),
    ("een appels", "appels", "incorrect", ()),
    ("man loopt huis", "De man loopt naar huis.", "incorrect", ()),
    # one slip in a word of four letters or more is almost; two from eight letters
    ("appl", "appel", "almost", ("spelling",)),
    ("apepl", "appel", "almost", ("spelling",)),
    ("fietsenwinkl", "fietsenwinkel", "almost", ("spelling",)),
    ("fitsenwinkl", "fietsenwinkel", "almost", ("spelling",)),
    ("fts", "fiets", "incorrect", ()),
    # a compound typed as two words is a slip too
    ("ik koop een fiets in de fietsen winkel", "Ik koop een fiets in de fietsenwinkel.", "almost", ("spelling",)),
    # short words have no slack
    ("dak", "dag", "incorrect", ()),
    # a slip that spells another known word is that word, not a slip
    ("kast", "kaas", "incorrect", ()),
    # a negation or a number is never a slip
    ("ik heb een tijd", "Ik heb geen tijd.", "incorrect", ()),
    ("ik kom net", "Ik kom niet.", "incorrect", ()),
    ("in 2025", "in 2024", "incorrect", ()),
    ("het kost 150 euro", "Het kost 1500 euro.", "incorrect", ()),
    # a different form of the verb is not a slip
    ("ik wonen in gent", "Ik woon in Gent.", "incorrect", ()),
    # one missing or extra function word in a longer sentence is almost; in a short one it is wrong
    ("ik woon gent", "Ik woon in Gent.", "almost", ("missing_word",)),
    ("ik woon wel in gent", "Ik woon in Gent.", "almost", ("extra_word",)),
    ("woon gent", "Ik woon in Gent.", "incorrect", ()),
    ("gent", "in Gent", "incorrect", ()),
    # a missing content word or negation is wrong at any length
    ("ik woon in", "Ik woon in Gent.", "incorrect", ()),
    ("ik woon niet in gent", "Ik woon in Gent.", "incorrect", ()),
    ("ik woon in gent", "Ik woon niet in Gent.", "incorrect", ()),
    # nothing typed is not an answer
    ("", "fiets", "incorrect", ()),
    ("   ", "fiets", "incorrect", ()),
])
def test_comparison_table(given, expected, outcome, notes):
    result = compare(given, expected, lexicon=LEXICON)
    assert (result.outcome, result.notes) == (outcome, notes), result


@pytest.mark.parametrize(("given", "expected", "article", "outcome", "notes"), [
    # a term item: a missing article is forgiven or almost, a wrong one is almost, an extra one is noted
    ("appel", "de appel", "optional", "correct", ("article_missing",)),
    ("appel", "de appel", "required", "almost", ("article_missing",)),
    ("het appel", "de appel", "optional", "almost", ("article",)),
    ("een huis", "het huis", "optional", "almost", ("article",)),
    ("de appel", "appel", "optional", "correct", ("article_extra",)),
    # the article alone is not the word
    ("de", "de appel", "optional", "incorrect", ()),
])
def test_article_policy_of_a_term(given, expected, article, outcome, notes):
    result = compare(given, expected, article=article)
    assert (result.outcome, result.notes) == (outcome, notes), result


def test_the_lexicon_is_read_like_a_typed_word():
    """Library terms carry their article and accents; the guard still knows them."""
    broek = compare("broek", "de broer", article="optional", lexicon=frozenset({"de broek"}))
    assert broek.outcome == "incorrect"
    geeerd = compare("ik heb veel geëerd", "Ik heb veel geleerd.", lexicon=frozenset({"geëerd"}))
    assert geeerd.outcome == "incorrect"


def test_the_kindest_accepted_answer_wins():
    result = compare("ik ben moe", ["Ik voel me moe.", "Ik ben moe."])
    assert result.outcome == "correct" and result.expected == "Ik ben moe."
    closest = compare("ik ben mooe", ["Ik voel me moe.", "Ik ben moe."])
    assert closest.outcome == "incorrect", "moe has three letters: no slack"
    assert closest.expected == "Ik ben moe.", "the diff is shown against the answer the learner aimed for"
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
    # words are paired with their closest counterpart, not by position
    assert compare("ik heb rood fiets", "Ik heb een rode fiets.").diff == (
        DiffOp("same", "ik", "ik"),
        DiffOp("same", "heb", "heb"),
        DiffOp("missing", "een"),
        DiffOp("changed", "rode", "rood"),
        DiffOp("same", "fiets", "fiets"),
    )
    assert compare("fietsen winkel", "fietsenwinkel").diff == (DiffOp("changed", "fietsenwinkel", "fietsen winkel"),)


def test_a_long_paste_is_not_compared_letter_by_letter():
    assert compare("x" * 200_000, "fietsenwinkel").outcome == "incorrect"


def test_the_building_blocks():
    assert fold("  ’s Morgens, “Goedemorgen!” ") == "'s morgens goedemorgen"
    assert fold("Hij zegt: ‘Ja.’") == "hij zegt ja"
    assert distance("appel", "apepl") == 1, "two neighbours swapped is one slip"
    assert distance("kitten", "sitting") == 3
    assert is_slip("appel", "appl") and not is_slip("appel", "appel")
    assert not is_slip("kaas", "kast", LEXICON)
    assert not is_slip("geen", "een") and not is_slip("1234", "1243")
