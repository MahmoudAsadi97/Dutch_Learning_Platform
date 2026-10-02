"""Versioned prompt for the video script writer."""
from __future__ import annotations

import json

from dlp.domains.stories.bible import StageProfile
from dlp.domains.stories.prompts import BELGIAN_DUTCH
from dlp.providers.base import ChatMessage

SCRIPT_VERSION = "video-script-v1"

SCRIPT_SYSTEM = (
    "Je schrijft het script van een korte video voor volwassenen die Nederlands leren in Vlaanderen. "
    "Eén presentator spreekt de kijker rechtstreeks aan, warm en duidelijk, zoals een goede taaldocent. "
    + BELGIAN_DUTCH + " "
    "Het script bestaat uit scènes: elke scène is wat de presentator zegt, drie tot zes korte zinnen, en bij elke "
    "scène hoort één kernwoord of korte uitdrukking die in beeld komt (keywords). "
    "Gebruik vooral woorden uit de lijst 'bekende woorden' en introduceer precies de gevraagde hoeveelheid nieuwe "
    "woorden; zet elk nieuw woord in de woordenlijst met een Engelse en een Perzische betekenis en de zin uit het "
    "script. Herhaal nieuwe woorden minstens twee keer in het script, dat helpt bij het onthouden. "
    "Elke zin van 'evidence' bij een vraag moet letterlijk in het script staan; de vragen toetsen begrip van wat "
    "gezegd werd. Geef per scène een Engelse en een Perzische vertaling (paragraphs_en, paragraphs_fa) die even lang "
    "zijn als de scènes. Geen regieaanwijzingen, geen titels in de gesproken tekst, geen uitleg buiten het JSON-object."
)

KIND_BRIEF = {
    "uitleg": ("Een presentator legt het onderwerp uit met voorbeelden uit het dagelijks leven in Vlaanderen: wat je "
               "zegt, wat je hoort, wat je doet. Eindig met één zin die de kijker aanmoedigt het zelf te proberen."),
    "verhaal": ("De presentator vertelt een kort, levendig verhaal over het onderwerp, met één klein probleem van elke "
                "dag en een goede afloop. Vertel het in de tegenwoordige tijd zodat de kijker meekijkt."),
}


def script_messages(*, profile: StageProfile, kind: str, topic: str, known_words: list[str],
                    candidate_words: list[str], target_seconds: int, feedback: str = "") -> list[ChatMessage]:
    brief = {
        "soort": kind,
        "onderwerp": topic or "iets uit het dagelijks leven in Vlaanderen",
        "niveau": profile.label,
        "lengte": (f"{profile.min_paragraphs}-{profile.max_paragraphs} scènes; ongeveer "
                   f"{(profile.min_words + profile.max_words) // 2} woorden in totaal, minstens {profile.min_words} en "
                   f"hoogstens {profile.max_words}; gesproken duurt dat ongeveer {target_seconds} seconden"),
        "zinnen": f"hoogstens {profile.max_sentence_words} woorden per zin, gemiddeld ongeveer {profile.mean_sentence_words:.0f}",
        "grammatica": profile.grammar,
        "aanwijzingen": profile.guidance,
        "nieuwe_woorden": f"precies {profile.new_words} nieuwe woorden, bij voorkeur uit 'kandidaat-woorden'",
    }
    user = (
        f"OPDRACHT\n{json.dumps(brief, ensure_ascii=False, indent=1)}\n\n"
        f"VORM\n{KIND_BRIEF.get(kind, KIND_BRIEF['uitleg'])}\n\n"
        f"BEKENDE WOORDEN (gebruik deze vrij)\n{', '.join(known_words[:220])}\n\n"
        f"KANDIDAAT-WOORDEN (kies hieruit de nieuwe woorden)\n{', '.join(candidate_words[:40])}\n"
    )
    if feedback:
        user += "\n" + feedback + "\nSchrijf het script opnieuw en geef het volledige JSON-object terug.\n"
    return [ChatMessage("system", SCRIPT_SYSTEM), ChatMessage("user", user)]
