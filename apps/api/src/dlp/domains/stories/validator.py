"""Deterministic quality gate for generated episodes.

The model proposes; this module decides. Checks are explainable and are fed back to the writer on a
retry. They do not judge literary quality or native-speaker correctness: that remains a human reviewer's
job, and every episode stays labelled as generated content.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from dlp.domains.stories.bible import StageProfile
from dlp.domains.stories.schemas import EpisodeDraft

# Frequent Dutch function and support words. Any of these count as known at every stage.
FUNCTION_WORDS: frozenset[str] = frozenset("""
de het een en of maar want dus ook nog al niet geen wel niets niemand iemand iets alles
ik je jij u hij zij ze we wij jullie me mij jou hem haar ons hen hun zich zijn mijn jouw uw onze
dit dat deze die daar hier er daarom daarna dan toen nu straks vandaag morgen gisteren later vroeger altijd nooit soms vaak
weer meer meest minder minst veel weinig erg heel zeer te zo ook even nog eens maar toch wel al
is ben bent zijn was waren wordt worden werd werden geweest geworden
heb hebt heeft hebben had hadden gehad
kan kunt kunnen kon konden wil wilt willen wilde wilden moet moeten moest moesten mag mogen mocht mochten
zal zult zullen zou zouden
ga gaat gaan ging gingen gegaan kom komt komen kwam kwamen gekomen doe doet doen deed deden gedaan
zie ziet zien zag zagen gezien zeg zegt zeggen zei zeiden gezegd weet weten wist wisten geweten
maak maakt maken maakte maakten gemaakt geef geeft geven gaf gaven gegeven neem neemt nemen nam namen genomen
sta staat staan stond stonden gestaan zit zitten zat zaten gezeten lig ligt liggen lag lagen gelegen
loop loopt lopen liep liepen gelopen kijk kijkt kijken keek keken gekeken vind vindt vinden vond vonden gevonden
denk denkt denken dacht dachten gedacht vraag vraagt vragen vroeg vroegen gevraagd laat laten liet lieten gelaten
blijf blijft blijven bleef bleven gebleven houd houdt houden hield hielden gehouden krijg krijgt krijgen kreeg kregen gekregen
hoor hoort horen hoorde hoorden gehoord word
in op aan bij van voor na naar met zonder over onder uit tot door om tegen tussen naast achter boven beneden
langs rond sinds per via
als wanneer waar wie wat welke welk hoe waarom hoeveel waarmee waarvan dat omdat terwijl hoewel zodat voordat nadat totdat ofwel
ja nee oké goed dank dankjewel bedankt alstublieft alsjeblieft graag sorry hallo dag goedemorgen goedemiddag goedenavond tot ziens
een twee drie vier vijf zes zeven acht negen tien elf twaalf dertien veertien vijftien zestien zeventien
achttien negentien twintig dertig veertig vijftig honderd duizend
eerste tweede derde laatste volgende vorige
maandag dinsdag woensdag donderdag vrijdag zaterdag zondag uur minuut minuten week weken maand maanden jaar jaren
mevrouw meneer mijnheer
groot klein nieuw oud jong goed slecht mooi lekker snel langzaam vroeg laat druk rustig blij moe
thuis huis straat stad weg werk school winkel bus trein fiets auto markt park station
iets niks oke ok hè hé allez amai zeker misschien natuurlijk eigenlijk gewoon echt
""".split())

ENGLISH_MARKERS: frozenset[str] = frozenset(
    "the and you with this that have from they were would what your there their about which when".split()
)

# Suffixes a known lemma may carry in the story (plurals, verb endings, diminutives, past participles).
_SUFFIXES = ("", "e", "en", "n", "s", "'s", "t", "te", "ten", "de", "den", "d", "je", "tje", "jes", "tjes", "er", "ers",
             "st", "ste", "ste", "ing", "ingen")
_TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?|\d+", re.UNICODE)
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(value.split())


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(normalise(text)) if not t.isdigit()]


def sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_END.split(text.strip()) if p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def lemma_key(term: str) -> str:
    """'de appel' -> 'appel', 'zich haasten' -> 'haasten', 'het huis (huizen)' -> 'huis'."""
    base = normalise(re.sub(r"\(.*?\)", "", term))
    words = [w for w in tokens(base) if w not in {"de", "het", "een", "zich", "te"}]
    return words[0] if len(words) == 1 else " ".join(words)


VOWELS = "aeou"


def stems_for(allowed: frozenset[str]) -> tuple[str, ...]:
    """Lemmas plus the verb stems they imply: 'kopen' -> 'kop', 'koop'; 'zoeken' -> 'zoek'."""
    stems: set[str] = set()
    for word in allowed | {w for w in FUNCTION_WORDS if len(w) >= 4}:
        if len(word) >= 4:
            stems.add(word)
        if word.endswith("en") and len(word) >= 5:
            stem = word[:-2]
            stems.add(stem)
            if len(stem) >= 3 and stem[-2] in VOWELS and stem[-1] not in VOWELS and stem[-3] != stem[-2]:
                stems.add(stem[:-1] + stem[-2] + stem[-1])
    return tuple(sorted((s for s in stems if len(s) >= 3), key=len, reverse=True))


def _known(token: str, allowed: frozenset[str], stems: tuple[str, ...], depth: int = 0) -> bool:
    if token in allowed or token in FUNCTION_WORDS:
        return True
    if len(token) < 4:
        return False
    stripped = token[2:] if token.startswith("ge") and len(token) > 6 else token
    for candidate in (token, stripped):
        for stem in stems:
            if len(stem) < 4 and len(candidate) > len(stem) + 2:
                continue
            if candidate.startswith(stem):
                rest = candidate[len(stem):]
                if rest in _SUFFIXES:
                    return True
                if depth == 0 and len(rest) >= 3:  # compound: fiets + en + winkel
                    for joiner in ("", "en", "s", "e"):
                        if rest.startswith(joiner) and _known(rest[len(joiner):], allowed, stems, depth + 1):
                            return True
            elif len(stem) >= 4 and stem.startswith(candidate) and len(stem) - len(candidate) <= 2:
                return True
    return False


def coverage(text_tokens: list[str], allowed: frozenset[str]) -> tuple[float, list[str]]:
    """Share of tokens that are function words, allowed vocabulary (with simple inflection), or names."""
    if not text_tokens:
        return 0.0, []
    stems = stems_for(allowed)
    unknown: list[str] = []
    known_count = 0
    for token in text_tokens:
        if _known(token, allowed, stems):
            known_count += 1
        else:
            unknown.append(token)
    return known_count / len(text_tokens), unknown


def term_in_text(term: str, text_tokens: list[str], text_norm: str) -> bool:
    key = lemma_key(term)
    if not key:
        return False
    if key in text_norm or normalise(term) in text_norm:
        return True
    words = frozenset(key.split())
    stems = stems_for(words)
    return any(_known(token, words, stems) for token in text_tokens if token not in FUNCTION_WORDS or token in words)


@dataclass
class ValidationResult:
    ok: bool
    hard: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def needs_retry(self) -> bool:
        return bool(self.hard) or len(self.warnings) >= 2

    def as_dict(self) -> dict:
        return {"ok": self.ok, "hard": list(self.hard), "warnings": list(self.warnings), "metrics": dict(self.metrics)}


def validate_draft(draft: EpisodeDraft, profile: StageProfile, *, allowed_vocabulary: frozenset[str],
                   cast_names: frozenset[str]) -> ValidationResult:
    hard: list[str] = []
    warnings: list[str] = []
    text = " ".join(draft.paragraphs)
    text_norm = normalise(text)
    all_tokens = tokens(text)
    word_count = len(text.split())
    sents = [s for p in draft.paragraphs for s in sentences(p)]
    sentence_lengths = [len(s.split()) for s in sents] or [0]

    # 1. Language: Dutch function words must dominate; English markers must be absent.
    function_share = sum(1 for t in all_tokens if t in FUNCTION_WORDS) / max(len(all_tokens), 1)
    english_share = sum(1 for t in all_tokens if t in ENGLISH_MARKERS) / max(len(all_tokens), 1)
    if function_share < 0.22 or english_share > 0.04:
        hard.append(f"not_dutch: function-word share {function_share:.2f}, english markers {english_share:.2f}")

    # 2. Length.
    if not profile.min_paragraphs <= len(draft.paragraphs) <= profile.max_paragraphs:
        (hard if len(draft.paragraphs) < 2 or len(draft.paragraphs) > profile.max_paragraphs + 2 else warnings).append(
            f"paragraph_count: {len(draft.paragraphs)} (wanted {profile.min_paragraphs}-{profile.max_paragraphs})")
    if word_count < profile.min_words * 0.6 or word_count > profile.max_words * 1.5:
        hard.append(f"word_count: {word_count} (wanted {profile.min_words}-{profile.max_words})")
    elif not profile.min_words <= word_count <= profile.max_words:
        warnings.append(f"word_count: {word_count} (wanted {profile.min_words}-{profile.max_words})")
    if len(draft.paragraphs_en) != len(draft.paragraphs):
        warnings.append(f"translation_count: {len(draft.paragraphs_en)} English paragraphs for {len(draft.paragraphs)} Dutch")

    # 3. Sentence complexity.
    longest = max(sentence_lengths)
    mean = sum(sentence_lengths) / len(sentence_lengths)
    if longest > profile.max_sentence_words + 6:
        hard.append(f"sentence_too_long: {longest} words (limit {profile.max_sentence_words})")
    elif longest > profile.max_sentence_words:
        warnings.append(f"sentence_too_long: {longest} words (limit {profile.max_sentence_words})")
    if mean > profile.mean_sentence_words + 2:
        warnings.append(f"sentences_too_complex: mean {mean:.1f} words (aim {profile.mean_sentence_words})")

    # 4. Regional forms: the serial models Belgian Standard Dutch; 'gij/ge' only ever as a labelled quirk.
    regional = [t for t in all_tokens if t in {"gij", "ge", "gulder", "gijle"}]
    if regional and not any(item.term.casefold() in {"gij", "ge"} for item in draft.glossary):
        hard.append("regional_form: 'gij/ge' used without a glossary label")

    # 5. Glossary terms must come from the text (inflected forms count: 'zoeken' is found as 'zoek').
    missing_terms = [item.term for item in draft.glossary if not term_in_text(item.term, all_tokens, text_norm)]
    if missing_terms:
        (hard if len(missing_terms) > len(draft.glossary) // 2 else warnings).append(
            "glossary_not_in_text: " + ", ".join(missing_terms[:6]))

    # 6. Questions must be answerable from the text: the evidence sentence has to exist.
    for index, question in enumerate(draft.questions):
        evidence = normalise(question.evidence).strip(" .!?\"'")
        if len(evidence) < 8 or evidence not in text_norm:
            hard.append(f"question_{index}_evidence_missing")

    # 7. Vocabulary coverage: known words plus the declared glossary.
    glossary_keys = {lemma_key(item.term) for item in draft.glossary}
    allowed = frozenset(allowed_vocabulary | glossary_keys | {normalise(n) for n in cast_names}
                        | {w for key in glossary_keys for w in key.split()})
    share, unknown = coverage(all_tokens, allowed)
    if share < profile.coverage - 0.15:
        hard.append(f"vocabulary_too_hard: {share:.2f} known (aim {profile.coverage:.2f}); unknown e.g. "
                    + ", ".join(sorted(set(unknown))[:10]))
    elif share < profile.coverage:
        warnings.append(f"vocabulary_above_level: {share:.2f} known (aim {profile.coverage:.2f}); unknown e.g. "
                        + ", ".join(sorted(set(unknown))[:10]))
    if len(draft.glossary) > profile.new_words + 4:
        warnings.append(f"too_many_new_words: {len(draft.glossary)} (aim {profile.new_words})")

    metrics = {"word_count": word_count, "paragraphs": len(draft.paragraphs), "sentences": len(sents),
               "longest_sentence": longest, "mean_sentence": round(mean, 1), "coverage": round(share, 3),
               "unknown_words": sorted(set(unknown))[:30], "function_share": round(function_share, 3),
               "glossary_terms": len(draft.glossary)}
    return ValidationResult(ok=not hard, hard=hard, warnings=warnings, metrics=metrics)


def feedback_text(result: ValidationResult) -> str:
    lines = ["FAILED CHECKS (fix every one, keep the same characters and plot):"]
    lines += [f"- {item}" for item in result.hard]
    lines += [f"- (improve) {item}" for item in result.warnings]
    return "\n".join(lines)
