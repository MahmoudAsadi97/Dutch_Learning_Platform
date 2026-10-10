"""Sentences cut into tiles for the sentence builder, and texts cut into sentences for ordering.

Dutch moves time words and adverbs around freely ("Morgen ga ik" and "Ik ga morgen"), and a comma usually
means a second clause that can come first; a sentence that opens with a prepositional phrase ("Voor de
wedstrijd oefent onze ploeg") can open with its subject instead. A tile grader that knows one order would mark
those right answers wrong, so a sentence becomes tiles only when it is one sentence with no comma, colon or
quotation, no movable time word and no opening preposition;
a longer sentence (10-20 words) becomes four to six chunks cut before conjunctions, so clauses stay whole.
The first word loses its capital when the same word appears in lower case elsewhere, so the capital does not
give the first tile away; a name keeps it. The final punctuation stays fixed after the tiles.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from dlp.domains.stories.validator import sentences

TILE_WORDS = (3, 9)
CHUNK_WORDS = (10, 20)
CHUNKS = (4, 6)
ORDER_SENTENCES = (3, 4)
ORDER_MAX_CHARS = 160
# words that may stand in several places of a Dutch sentence
MOVABLE = frozenset({
    "vandaag", "morgen", "gisteren", "overmorgen", "eergisteren", "nu", "straks", "vanavond", "vanmiddag",
    "vanochtend", "vanmorgen", "vannacht", "soms", "altijd", "vaak", "nooit", "daarna", "toen", "eerst", "later",
    "dan", "meestal", "zelden", "graag", "ook", "misschien", "natuurlijk", "eigenlijk", "gelukkig", "helaas",
})
PREPOSITIONS = frozenset({"in", "op", "aan", "naar", "van", "met", "voor", "bij", "uit", "om", "over", "tot", "door",
                          "tegen", "onder", "achter", "naast", "tussen", "sinds", "zonder", "na", "tijdens", "volgens",
                          "binnen", "buiten", "rond", "langs", "vanaf", "dankzij", "ondanks"})
CONJUNCTIONS = frozenset({"en", "maar", "want", "omdat", "dat", "als", "die", "wanneer", "terwijl", "of", "zodat",
                          "hoewel", "voordat", "nadat", "waar", "wat", "dus"})
_CLAUSE_MARK = re.compile(r"[,;:()\"“”‘’!?…]")
_END = re.compile(r"[.!?…]+$")


def lower_words(texts: Iterable[str]) -> frozenset[str]:
    """Words that occur in lower case somewhere other than at the start of a sentence."""
    found: set[str] = set()
    for text in texts:
        for sentence in sentences(text):
            found.update(word for word in (w.strip(".,!?;:\"“”‘’()…") for w in sentence.split()[1:]) if word.islower())
    return frozenset(found)


def _movable(words: list[str]) -> bool:
    return bool({word.lower().strip(",") for word in words} & MOVABLE) or words[0].lower() in PREPOSITIONS


def _body(sentence: str) -> tuple[list[str], str] | None:
    sentence = sentence.strip()
    if len(sentences(sentence)) != 1:
        return None
    end = _END.search(sentence)
    words = sentence[: end.start()].split() if end else sentence.split()
    if not words or any(_CLAUSE_MARK.search(word) for word in words):
        return None
    return words, end.group(0) if end else ""


def _uncapitalise(words: list[str], lower: frozenset[str]) -> list[str]:
    first = words[0]
    return [first.lower() if first.lower() in lower else first, *words[1:]]


def tiles(sentence: str, lower: frozenset[str]) -> tuple[list[str], str] | None:
    """The words of a short sentence in order, and its final punctuation; None when another order could be right."""
    body = _body(sentence)
    if body is None:
        return None
    words, end = body
    if not TILE_WORDS[0] <= len(words) <= TILE_WORDS[1] or _movable(words):
        return None
    return _uncapitalise(words, lower), end


def chunks(sentence: str, lower: frozenset[str]) -> tuple[list[str], str] | None:
    """A longer sentence as four to six word groups, cut before conjunctions and then evenly."""
    sentence = sentence.strip()
    if len(sentences(sentence)) != 1:
        return None
    end = _END.search(sentence)
    body = sentence[: end.start()] if end else sentence
    if re.search(r"[;:()\"“”‘’!?]", body):
        return None
    words = body.replace(",", " , ").split()
    if not CHUNK_WORDS[0] <= sum(word != "," for word in words) <= CHUNK_WORDS[1] or _movable(words):
        return None
    groups: list[list[str]] = [[]]
    for word in words:
        if word == ",":
            if groups[-1]:
                groups[-1][-1] += ","
                groups.append([])
            continue
        if word.lower() in CONJUNCTIONS and groups[-1]:
            groups.append([])
        groups[-1].append(word)
    groups = [group for group in groups if group]
    while len(groups) < CHUNKS[0]:
        longest = max(range(len(groups)), key=lambda i: len(groups[i]))
        if len(groups[longest]) < 4:
            return None
        half = len(groups[longest]) // 2
        groups[longest: longest + 1] = [groups[longest][:half], groups[longest][half:]]
    if len(groups) > CHUNKS[1]:
        return None
    groups[0] = _uncapitalise(groups[0], lower)
    return [" ".join(group) for group in groups], end.group(0) if end else ""


def order_run(text: str) -> list[str] | None:
    """Three or four consecutive sentences of a text to put back in order, or None when the text is too short."""
    parts = sentences(text)
    run = [part for part in parts if len(part) <= ORDER_MAX_CHARS]
    if len(run) != len(parts) or len(parts) < ORDER_SENTENCES[0]:
        return None
    return parts[: ORDER_SENTENCES[1]]
