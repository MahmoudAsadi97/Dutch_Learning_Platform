"""Versioned prompts for the story writer and the on-demand translator."""
from __future__ import annotations

import json

from dlp.domains.stories.bible import StageProfile
from dlp.providers.base import ChatMessage

WRITER_VERSION = "story-episode-v1"
TRANSLATE_VERSION = "story-translate-v1"

BELGIAN_DUTCH = (
    "Schrijf Belgisch Standaardnederlands zoals het in Vlaanderen verzorgd wordt gebruikt: 'namiddag' voor afternoon, "
    "'lokaal' voor een zaal in een openbaar gebouw, 'plezant' alleen als jongerentaal met label. Gebruik 'u' aan een "
    "loket of in een winkel en 'je' tussen vrienden en familie. Gebruik geen dialect en geen 'gij/ge', behalve als een "
    "personage het één keer zegt en de woordenlijst het als regionaal markeert. Vermijd typisch Nederlandse vormen "
    "zoals 'hartstikke', 'joh', 'jongens' als aanspreking en 'middag' voor 14 uur."
)

WRITER_SYSTEM = (
    "Je bent de schrijver van een doorlopend feuilleton voor volwassenen die Nederlands leren in Vlaanderen. "
    "Elke aflevering is een kort, levendig verhaal met echte dialoog, humor en één klein probleem van elke dag. "
    + BELGIAN_DUTCH + " "
    "De lezer leert de taal: gebruik vooral woorden uit de lijst 'bekende woorden' en introduceer precies de gevraagde "
    "hoeveelheid nieuwe woorden; zet elk nieuw woord in de woordenlijst met een Engelse en een Perzische betekenis en de "
    "zin uit het verhaal. Elke zin van 'evidence' bij een vraag moet letterlijk in het verhaal staan. "
    "De vragen toetsen begrip van het verhaal, niet algemene kennis; de drie antwoordopties zijn kort en verschillend. "
    "Het verhaal eindigt met een open moment waarop de lezer een keuze maakt voor de volgende aflevering. "
    "Geen titels zoals 'Aflevering 3' in de tekst. Geen uitleg buiten het JSON-object."
)


def writer_messages(*, profile: StageProfile, bible: dict, memory: list[dict], known_words: list[str],
                    candidate_words: list[str], theme: str, previous_choice: str, episode_number: int,
                    feedback: str = "") -> list[ChatMessage]:
    cast = [f"- {c['name']} ({c['age']}): {c['role']}. Karakter: {c['trait']}. Spreekt: {c['speech']}" for c in bible["cast"]]
    recent = [f"- Aflevering {m['number']} ({m.get('title', '')}): {m['recap']}" for m in memory[-4:]]
    brief = {
        "aflevering": episode_number,
        "niveau": profile.label,
        "lengte": (f"{profile.min_paragraphs}-{profile.max_paragraphs} alinea's; ongeveer "
                   f"{(profile.min_words + profile.max_words) // 2} woorden in totaal, minstens {profile.min_words} "
                   f"en hoogstens {profile.max_words}"),
        "zinnen": f"hoogstens {profile.max_sentence_words} woorden per zin, gemiddeld ongeveer {profile.mean_sentence_words:.0f}",
        "grammatica": profile.grammar,
        "aanwijzingen": profile.guidance,
        "nieuwe_woorden": f"precies {profile.new_words} nieuwe woorden, bij voorkeur uit 'kandidaat-woorden'",
        "thema": theme or "vrij te kiezen, iets uit het dagelijks leven in de straat",
        "keuze_van_de_lezer_voor_deze_aflevering": previous_choice or "geen; dit is een nieuw begin",
    }
    user = (
        f"WERELD\n{bible['setting']['description_nl']}\nPlaatsen: {', '.join(bible['setting']['places'])}\n\n"
        f"PERSONAGES\n" + "\n".join(cast) + "\n\n"
        "REGELS\n" + "\n".join(f"- {r}" for r in bible["rules"]) + "\n\n"
        "WAT ER AL GEBEURD IS\n" + ("\n".join(recent) if recent else "- Dit is de eerste aflevering.") + "\n\n"
        f"OPDRACHT\n{json.dumps(brief, ensure_ascii=False, indent=1)}\n\n"
        f"BEKENDE WOORDEN (gebruik deze vrij)\n{', '.join(known_words[:220])}\n\n"
        f"KANDIDAAT-WOORDEN (kies hieruit de nieuwe woorden)\n{', '.join(candidate_words[:40])}\n"
    )
    if feedback:
        user += "\n" + feedback + "\nSchrijf de aflevering opnieuw en geef het volledige JSON-object terug.\n"
    return [ChatMessage("system", WRITER_SYSTEM), ChatMessage("user", user)]


def translate_messages(paragraph: str, language: str) -> list[ChatMessage]:
    target = {"fa": "Persian (Farsi)", "en": "English"}.get(language, language)
    return [
        ChatMessage("system", f"Translate the Dutch paragraph into natural {target} for an adult learner. Keep names "
                              "unchanged. Return only the translation in the JSON field 'translation'."),
        ChatMessage("user", paragraph),
    ]
