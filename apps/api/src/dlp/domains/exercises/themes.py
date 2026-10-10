"""Library topics that belong to one theme, for odd one out.

The beginner word lists come back to a theme further down the list (Keuken and Kookgerei, Lichaam and
Lichaamsdelen, Familie and Generaties), so distance in the topic order alone does not make a word the odd
one: a fork is not odd among a plate, a bowl and a spoon. A word from a topic in the same theme as the group's
topic is never the odd word. Topics may sit in more than one theme; a topic in none is related only to
itself. tests/test_exercise_generators.py checks that every label here exists in the library.
"""
from __future__ import annotations

THEMES: tuple[frozenset[str], ...] = tuple(frozenset(theme) for theme in (
    # pre-A1, A1, pre-A2
    {"Thuis", "Wonen", "Meubels", "Badkamer", "Binnenhuis", "In het gebouw", "Verhuizen", "Huren", "Huishouden",
     "Schoonmaken", "Bezoek thuis", "Keuken", "Kookgerei", "Afval"},
    {"Familie", "Generaties", "Personen", "Van wie?", "Bezoek thuis"},
    {"Keuken", "Drinken", "Ontbijt", "Fruit", "Groenten", "Koken", "Smaak", "Eten maken", "Kookgerei", "Restaurant",
     "Winkelen", "Iets kopen"},
    {"Kleding", "Winterkleding", "Verzorgen", "Badkamer", "Kleuren"},
    {"Vervoer", "Trein", "Fietsen", "Straat", "De weg", "Onderweg", "Verplaatsen", "Reizen", "Plaats", "Buurt",
     "Landschap", "Bewegen"},
    {"Winkelen", "Geld", "Iets kopen", "Handel", "Post"},
    {"Les", "Schrijven", "Leren", "Taal", "Vraagwoorden", "Zinnen verbinden", "Beleefd spreken", "Begroeten",
     "Hulp vragen", "Gegevens"},
    {"Telefoon", "Computer", "Post", "Afspreken"},
    {"Tijd", "Weekdagen", "Kloktijd", "Dagritme", "Volgorde", "Gewoontes", "Seizoenen", "Wachten", "Afspreken"},
    {"Weer", "Seizoenen", "Tuin", "Dieren", "Park", "Landschap", "Winterkleding"},
    {"Lichaam", "Gezicht", "Lichaamsdelen", "Gezondheid", "Apotheek", "Zorg", "Verzorgen", "Sport", "Bewegen"},
    {"Vrije tijd", "Sport", "Muziek", "Uitgaan", "Feest", "Kunst", "Bewegen", "Nieuwe ervaringen", "Afspreken",
     "Restaurant", "Park"},
    {"Werk", "Een job zoeken", "Gereedschap", "Maken", "Handel"},
    {"Tellen", "Aantallen", "Grotere getallen", "Hoeveelheid", "Afmetingen", "Geld", "Kloktijd"},
    {"Gevoelens", "Behoeften", "Moeite", "Herinneringen", "Vooruitgang", "Mogelijkheden", "Nieuwe ervaringen"},
    # A2, pre-B1, B1
    {"Documenten", "Hulp en diensten", "Geldzaken", "Huurafspraken"},
    {"Op reis", "Vervoer", "Wegwijs in het station", "Reisplanning", "Onderweg"},
    {"Wonen", "Meubels", "Problemen in huis", "Huurafspraken", "Toestellen", "In de tuin", "In de keuken"},
    {"In de keuken", "Samen koken", "Eten kopen", "In het café", "Uit eten", "Bewust kopen"},
    {"Bij de huisarts", "Het lichaam", "Bewegen", "Sportmateriaal"},
    {"Beroepen", "Veilig aan het werk", "Mensen op het werk", "Werk organiseren"},
    {"Studeren", "Leren leren", "Taal oefenen", "Nieuws begrijpen"},
    {"Contact houden", "Digitaal contact", "Afspreken en plannen", "Omgaan met mensen", "Familie", "Gevoelens",
     "Samen problemen oplossen", "Samen beslissen", "Een mening uitleggen", "Een plan beoordelen",
     "Meedoen in de buurt", "In de buurt", "Een activiteit organiseren", "Vrije tijd"},
    {"Het weer", "Natuur dichtbij", "In de tuin", "Minder afval"},
    {"Winkelen", "Kleding", "Bewust kopen", "Eten kopen", "Geldzaken"},
    {"Tijd en gewoontes", "Afspreken en plannen"},
))


def related(topic: str, other: str) -> bool:
    return topic == other or any(topic in theme and other in theme for theme in THEMES)
