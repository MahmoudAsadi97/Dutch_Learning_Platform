"""Sentences cut into tiles for the sentence builder, and texts cut into sentences for ordering.

Dutch puts many things first: a time word or phrase ("Morgen ga ik", "De volgende dag ging ik"), an adverb
("Samen bedachten ze", "Daardoor ben ik blij"), a prepositional phrase ("Voor de wedstrijd oefent onze ploeg"),
a subordinate clause ("Als het regent, blijf ik thuis"); words joined by en or of swap freely ("moeder en
vader"). A tile grader that knows one order would mark those right answers wrong. So word tiles come only from
one plain sentence of three to nine words that opens with its subject (an article, a determiner, a possessive,
a pronoun, a numeral or a name), has no comma, colon or quotation, no en or of, and no movable time word or
adverb. A sentence of ten to twenty words that opens with its subject becomes four to six chunks instead, cut
before conjunctions and then evenly; commas stay inside a chunk. A prepositional phrase in the middle can
still move ("Ik ga naar school" / "Naar school ga ik"): the learner may then overrule the check, and a built
sentence never writes a mistake (D-29).

The first word loses its capital when it is a function word or appears in lower case elsewhere in the stage's
texts, so the capital does not give the first piece away; a name keeps it. The final punctuation stays fixed
after the pieces.
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
    "daardoor", "daarom", "daarop", "daar", "hier", "samen", "weer", "nog", "al", "toch", "thuis", "zo", "dus",
    "vooral", "tegelijk", "naderhand", "vooralsnog", "uiteindelijk", "eindelijk", "regelmatig", "opnieuw", "meteen",
    "telkens", "online", "vooraf", "boven", "beneden", "binnen", "buiten", "intussen", "ondertussen", "sindsdien",
    "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag",
})
TIME_NOUNS = frozenset({"dag", "week", "maand", "jaar", "avond", "ochtend", "middag", "nacht", "keer", "zomer",
                        "winter", "lente", "herfst", "weekend", "dagen", "weken", "maanden", "jaren", "uur", "minuut"})
PREPOSITIONS = frozenset({"in", "op", "aan", "naar", "van", "met", "voor", "bij", "uit", "om", "over", "tot", "door",
                          "tegen", "onder", "achter", "naast", "tussen", "sinds", "zonder", "na", "tijdens", "volgens",
                          "binnen", "buiten", "rond", "langs", "vanaf", "dankzij", "ondanks"})
CONJUNCTIONS = frozenset({"en", "maar", "want", "omdat", "dat", "als", "die", "wanneer", "terwijl", "of", "zodat",
                          "hoewel", "voordat", "nadat", "waar", "wat", "dus"})
# words a sentence that opens with its subject may start with (a capitalised word not lower elsewhere is a name)
SUBJECT_STARTS = frozenset({
    "de", "het", "een", "deze", "die", "dit", "dat", "mijn", "jouw", "je", "zijn", "haar", "ons", "onze", "hun", "uw",
    "ik", "jij", "hij", "zij", "ze", "wij", "we", "jullie", "u", "men", "iemand", "niemand", "iedereen", "alles",
    "niets", "veel", "weinig", "alle", "sommige", "beide", "geen", "één", "twee", "drie", "vier", "vijf", "zes",
    "zeven", "acht", "negen", "tien",
})
# function words, numerals and names of days and months: never a name, always lower case inside a sentence
ALWAYS_LOWER = SUBJECT_STARTS | CONJUNCTIONS | PREPOSITIONS | MOVABLE | frozenset({
    "elke", "iedere", "welke", "waarom", "hoe", "wie", "wanneer", "januari", "februari", "maart", "april", "mei",
    "juni", "juli", "augustus", "september", "oktober", "november", "december", "kun", "kan", "wil", "mag", "moet",
})
_CLAUSE_MARK = re.compile(r"[,;:()\"“”‘’!?…]")
_END = re.compile(r"[.!?…]+$")


def lower_words(texts: Iterable[str]) -> frozenset[str]:
    """Words that occur in lower case somewhere other than at the start of a sentence, and the function words."""
    found: set[str] = set(ALWAYS_LOWER)
    for text in texts:
        for sentence in sentences(text):
            found.update(word for word in (w.strip(".,!?;:\"“”‘’()…") for w in sentence.split()[1:]) if word.islower())
    return frozenset(found)


def _lowered(word: str) -> str:
    # "Eén" lowered is "één", not "eén"
    return "één" if word.lower() == "eén" else word.lower()


def _opens_with_subject(words: list[str], lower: frozenset[str]) -> bool:
    first = _lowered(words[0])
    if first in MOVABLE or first in PREPOSITIONS or set(_lowered(w) for w in words[:3]) & TIME_NOUNS:
        return False  # a time word or phrase, an adverb or a prepositional phrase first: it can move
    return first in SUBJECT_STARTS or (words[0][:1].isupper() and first not in lower)  # or a name


def _movable(words: list[str], lower: frozenset[str]) -> bool:
    return bool({_lowered(word).strip(",") for word in words} & MOVABLE) or not _opens_with_subject(words, lower)


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
    first = _lowered(words[0])
    return [first if first in lower else words[0], *words[1:]]


def tiles(sentence: str, lower: frozenset[str]) -> tuple[list[str], str] | None:
    """The words of a short sentence in order, and its final punctuation; None when another order could be right."""
    body = _body(sentence)
    if body is None:
        return None
    words, end = body
    if not TILE_WORDS[0] <= len(words) <= TILE_WORDS[1] or _movable(words, lower):
        return None
    if {_lowered(word) for word in words} & {"en", "of"}:
        return None  # "moeder en vader", "vader en moeder"
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
    if not CHUNK_WORDS[0] <= sum(word != "," for word in words) <= CHUNK_WORDS[1] or _movable(words, lower):
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
