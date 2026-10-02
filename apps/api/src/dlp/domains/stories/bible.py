"""The serial's fixed world and the per-stage writing constraints.

Everything here is original teaching fiction. The cast is deliberately small so that episodes stay
coherent for a model with a short memory, and the town is invented so that no real place or person is
described.
"""
from __future__ import annotations

from dataclasses import dataclass

SERIES_TITLE = "De Lindestraat"
TOWN = "Zilverdonk"

DEFAULT_BIBLE: dict = {
    "version": 1,
    "title": SERIES_TITLE,
    "setting": {
        "town": TOWN,
        "description_nl": (
            f"{TOWN} is een klein stadje aan de Leie in Vlaanderen. De verhalen spelen zich af in en rond de "
            "Lindestraat: de bakkerij op de hoek, de fietsenwinkel De Trapper, het buurtloket, het station, "
            "het park en de zaterdagmarkt."
        ),
        "places": [
            "de bakkerij op de hoek", "fietsenwinkel De Trapper", "het buurtloket", "het station",
            "het park", "de zaterdagmarkt", "de bibliotheek", "het café De Lindeboom", "de bushalte", "de school",
        ],
    },
    "cast": [
        {"name": "Sami", "age": 29,
         "role": "fietsenmaker bij De Trapper; woont sinds twee jaar in Zilverdonk en leert Nederlands",
         "trait": "nieuwsgierig, beleefd, durft fouten te maken en vraagt door",
         "speech": "spreekt rustig en duidelijk; gebruikt 'u' tegen klanten"},
        {"name": "mevrouw De Clercq", "age": 71, "role": "buurvrouw van Sami; gepensioneerde lerares",
         "trait": "precies, warm, houdt van haar tuin en van correcte taal",
         "speech": "spreekt verzorgd Standaardnederlands"},
        {"name": "Ayşe", "age": 45, "role": "bakker; runt de bakkerij op de hoek",
         "trait": "direct, hartelijk, weet alles wat er in de straat gebeurt",
         "speech": "kort en vriendelijk; noemt iedereen bij de voornaam"},
        {"name": "Tom", "age": 38, "role": "postbode; altijd gehaast; supporter van KV Zilverdonk",
         "trait": "grappig, soms slordig, altijd bereid te helpen", "speech": "spreekt snel; zegt vaak 'allez' en 'amai'"},
        {"name": "Lotte", "age": 17, "role": "kleindochter van mevrouw De Clercq; zit in het zesde middelbaar",
         "trait": "luid, slim, altijd met haar telefoon bezig", "speech": "jongerentaal; zegt 'je' en 'jij' tegen iedereen"},
        {"name": "Baas", "age": 11, "role": "de oude hond van de bakkerij", "trait": "lui, maar dol op koekjes",
         "speech": "blaft"},
    ],
    "rules": [
        "Het verhaal speelt in het heden, in Vlaanderen.",
        "Kleine problemen van elke dag; nooit geweld, ziekte als drama, romantiek, religie of politiek.",
        "Personages zijn vriendelijk voor elkaar; humor is licht.",
        "Sami is geen leerling van de lezer en geeft geen taalles; hij maakt zelf kleine fouten die anderen "
        "vriendelijk verbeteren.",
    ],
}


@dataclass(frozen=True)
class StageProfile:
    stage_id: str
    label: str
    min_paragraphs: int
    max_paragraphs: int
    min_words: int
    max_words: int
    max_sentence_words: int
    mean_sentence_words: float
    new_words: int
    coverage: float  # share of tokens that must be known (function words, stage vocabulary, saved words, glossary)
    grammar: str
    guidance: str


PROFILES: dict[str, StageProfile] = {p.stage_id: p for p in (
    StageProfile("pre-a1", "pre-A1", 3, 4, 40, 95, 10, 6.5, 4, 0.82,
                 "alleen tegenwoordige tijd; 'ik ben', 'ik heb', 'ik ga'; getallen tot twintig; dagen; geen bijzinnen",
                 "Heel korte zinnen. Herhaal belangrijke woorden. Eén handeling per zin."),
    StageProfile("a1", "A1", 3, 4, 60, 130, 12, 8.0, 5, 0.80,
                 "tegenwoordige tijd; kunnen, willen, moeten; vragen met waar/wanneer/hoeveel; tijd en prijs; "
                 "'en', 'maar', 'want'",
                 "Korte zinnen. Veel dialoog met korte beurten. Concrete dingen: eten, winkel, bus, huis, werk."),
    StageProfile("pre-a2", "pre-A2", 3, 5, 90, 165, 14, 9.0, 6, 0.78,
                 "tegenwoordige tijd en perfectum (heb gekocht, is gegaan); scheidbare werkwoorden; 'omdat' mag één keer",
                 "Zinnen blijven kort. Eén verrassing in het verhaal. Dialoog met beleefde vormen aan een loket of in "
                 "een winkel."),
    StageProfile("a2", "A2", 4, 5, 120, 200, 16, 10.0, 7, 0.75,
                 "perfectum en imperfectum van frequente werkwoorden; bijzinnen met omdat, als, dat; vergelijkingen",
                 "Een klein probleem dat opgelost wordt. Afspraken, tijden en plaatsen moeten kloppen met elkaar."),
    StageProfile("pre-b1", "pre-B1", 4, 5, 150, 240, 18, 11.0, 8, 0.72,
                 "verbindingswoorden (daarom, toen, terwijl, hoewel); zou graag; passief één keer",
                 "Personages hebben een mening en leggen die uit. Een misverstand dat uitgepraat wordt."),
    StageProfile("b1", "B1", 4, 6, 180, 280, 20, 12.0, 8, 0.68,
                 "betrekkelijke bijzinnen (die, dat, waar); hypotheses met 'zou'; indirecte rede",
                 "Een dilemma met twee kanten. Laat een personage argumenteren."),
    StageProfile("pre-b2", "pre-B2", 4, 6, 210, 320, 22, 13.0, 10, 0.64,
                 "nuances met modale partikels (toch, wel, eens, maar); formele en informele registers naast elkaar",
                 "Twee verhaallijnen die samenkomen. Eén officieel document of gesprek (gemeente, verzekering, "
                 "werk)."),
    StageProfile("b2", "B2", 5, 6, 250, 360, 24, 14.0, 10, 0.60,
                 "complexe zinnen; uitdrukkingen die in Vlaanderen gangbaar zijn, gemarkeerd in de woordenlijst",
                 "Ironie mag. Een beslissing met gevolgen voor latere afleveringen."),
    StageProfile("pre-c1", "pre-C1", 5, 7, 290, 400, 26, 15.0, 12, 0.56,
                 "stijlvariatie; nominalisaties; precieze woordkeuze",
                 "Maatschappelijk thema uit het dagelijks leven (wonen, werk, buurt), nooit partijpolitiek."),
    StageProfile("c1", "C1", 5, 7, 320, 440, 28, 16.0, 12, 0.52,
                 "literaire middelen met mate; impliciete informatie die de lezer moet afleiden",
                 "Perspectiefwisseling mag. Laat iets ongezegd dat de vragen kunnen toetsen."),
    StageProfile("pre-c2", "pre-C2", 5, 7, 340, 470, 30, 17.0, 14, 0.48,
                 "idiomen en registerwissels, gemarkeerd; subtiele toon",
                 "Een moreel kleine, menselijke keuze; geen moraliserend einde."),
    StageProfile("c2", "C2", 5, 8, 360, 500, 32, 18.0, 14, 0.45,
                 "volledige stilistische vrijheid binnen de Belgische standaardtaal",
                 "Dubbele bodem toegestaan. Toon en ritme dragen het verhaal."),
)}

STAGE_ORDER = list(PROFILES)


def profile_for(stage_id: str) -> StageProfile:
    try:
        return PROFILES[stage_id]
    except KeyError as exc:
        raise ValueError(f"unknown stage {stage_id}") from exc


def stages_up_to(stage_id: str) -> list[str]:
    """The stage and every lower stage, for cumulative vocabulary."""
    return STAGE_ORDER[: STAGE_ORDER.index(stage_id) + 1]
