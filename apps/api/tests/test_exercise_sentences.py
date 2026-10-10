"""Which sentences become tiles, chunks or an ordering item, and why others do not."""
from __future__ import annotations

import pytest

from dlp.domains.exercises.sentences import chunks, lower_words, order_run, tiles

LOWER = lower_words(["Ik zie dat ik de bus mis.", "Soms ga ik met de fiets.", "Zij woont in het centrum van Gent."])


@pytest.mark.parametrize(("sentence", "expected"), [
    ("Ik neem de bus naar school.", (["ik", "neem", "de", "bus", "naar", "school"], ".")),
    ("Sara woont in Gent.", (["Sara", "woont", "in", "Gent"], ".")),  # a name keeps its capital
    ("Eén kat slaapt.", (["één", "kat", "slaapt"], ".")),
    # another order would be right too: a question word, an adverb or a time phrase first, a movable word,
    # an opening preposition or clause, words joined by en or of
    ("Waar woon je?", None),
    ("Daardoor ben ik weer blij.", None),
    ("Samen bedachten ze een plan.", None),
    ("De volgende dag ging ik weg.", None),
    ("Mijn moeder en vader staan op de foto.", None),
    ("Morgen ga ik naar school.", None),
    ("Ik ga morgen naar school.", None),
    ("Voor de les drink ik koffie.", None),
    ("Als het regent, blijf ik thuis.", None),
    ("Hij zegt: kom binnen.", None),
    # too short, too long, or two sentences
    ("Ja hoor.", None),
    ("Ik neem elke dag de bus naar school en ik lees een boek.", None),
    ("Ik lees. Jij schrijft een brief.", None),
])
def test_tiles(sentence, expected):
    assert tiles(sentence, LOWER) == expected


def test_a_longer_sentence_becomes_whole_clauses():
    pieces, end = chunks("Ik blijf vandaag thuis omdat ik ziek ben en mijn moeder komt koken.", LOWER) or ([], "")
    assert pieces == [], "a movable time word: no chunks"
    pieces, end = chunks("Het boek kost twaalf euro, niet elf, en ik betaal met twintig.", LOWER)
    assert pieces == ["het boek", "kost twaalf euro,", "niet elf,", "en ik betaal met twintig"] and end == "."
    assert 4 <= len(pieces) <= 6
    assert chunks("Ik neem de bus.", LOWER) is None


def test_ordering_needs_three_short_sentences():
    assert order_run("Ik sta op. Ik eet. Ik ga naar het werk. Ik werk tot vijf uur. Dan ga ik naar huis.") == [
        "Ik sta op.", "Ik eet.", "Ik ga naar het werk.", "Ik werk tot vijf uur."]
    assert order_run("Ik sta op. Ik eet.") is None
    assert order_run("Ik sta op. " + "Ik " + "lees " * 60 + "een boek. Ik slaap.") is None
