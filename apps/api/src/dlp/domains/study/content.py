"""Adapt real, indexed teaching sources into one predictable study journey.

Catalogue entries are taxonomy, not a claim that an exercise has been authored.
Only explicit source references make a topic available. No GET generates content,
awards progress, or asks a language model to invent a lesson.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import service, supplements
from dlp.domains.curriculum.coverage import eligible_story_ids
from dlp.domains.curriculum.library import LibraryWord, library_for, normalise
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS, Skill
from dlp.domains.curriculum.topics import PracticeTopic, topics_for
from dlp.domains.study.reading_sources import read_reading_batches, reading_paths
from dlp.domains.study.schemas import (
    CheckQuestion,
    IndexDocument,
    PackDocument,
    ReadingDocument,
    ReadingLesson,
    ReadingMapDocument,
    SourceListeningDocument,
    TopicDocument,
)

GROUPS = {
    "culture": ("Cultuur", "Culture"), "daily": ("Dagelijks leven", "Daily life"),
    "digital": ("Digitale wereld", "Digital life"), "environment": ("Natuur en milieu", "Nature and environment"),
    "ideas": ("Ideeën en toekomst", "Ideas and the future"), "leisure": ("Vrije tijd", "Leisure"),
    "money": ("Geld en wonen", "Money and housing"), "people": ("Mensen en relaties", "People and relationships"),
    "places": ("Plaatsen en reizen", "Places and travel"), "services": ("Diensten", "Services"),
    "society": ("Samenleving", "Society"), "study": ("Studeren", "Study"),
    "wellbeing": ("Gezondheid en welzijn", "Health and wellbeing"), "work": ("Werk", "Work"),
}


def copy(nl: str, en: str) -> dict[str, str]:
    return {"nl": nl, "en": en}


def bilingual(value) -> dict[str, str]:
    if isinstance(value, dict):
        return copy(value["nl"], value["en"])
    return copy(value.nl, value.en)


@lru_cache(maxsize=4)
def _documents(root: str, topic_stamp: int, index_stamp: int):
    path = Path(root)
    topics = TopicDocument.model_validate_json((path / "topics.json").read_text(encoding="utf-8"))
    index = IndexDocument.model_validate_json((path / "stage-index.json").read_text(encoding="utf-8"))
    known = {topic.id for topic in topics.topics}
    for stage_id, skills in index.stages.items():
        if stage_id not in STAGE_IDS or set(skills) != set(SKILLS):
            raise ValueError("guided index requires known stages and all four skill maps")
        for mapped in skills.values():
            if not set(mapped).issubset(known):
                raise ValueError("guided index refers to an unknown topic")
            for sources in mapped.values():
                if len({(item.source, item.id) for item in sources}) != len(sources):
                    raise ValueError("guided index repeats a source")
                if len({item.id for item in sources}) != len(sources):
                    raise ValueError("guided activity IDs must be unambiguous within a topic")
    return topics, index


def documents():
    root = CONTENT_DIR / "study"
    return _documents(str(root), (root / "topics.json").stat().st_mtime_ns,
                      (root / "stage-index.json").stat().st_mtime_ns)


@lru_cache(maxsize=24)
def _pack(path: str, modified: int) -> PackDocument:
    document = PackDocument.model_validate_json(Path(path).read_text(encoding="utf-8"))
    if document.stage_id != Path(path).stem:
        raise ValueError("guided pack does not match its stage")
    return document


def pack_for(stage_id: str) -> PackDocument | None:
    require_stage(stage_id)
    path = CONTENT_DIR / "study" / "packs" / f"{stage_id}.json"
    return _pack(str(path), path.stat().st_mtime_ns) if path.exists() else None


@lru_cache(maxsize=24)
def _readings(root: str, stage_id: str, version: tuple) -> tuple[ReadingLesson, ...]:
    lessons = []
    identities: set[str] = set()
    plots: set[str] = set()
    for _, path, data in read_reading_batches(Path(root), stage_id):
        document = ReadingDocument.model_validate(data)
        for lesson in document.lessons:
            plot = normalise(lesson.plot_key)
            if lesson.id in identities or plot in plots:
                raise ValueError(f"{path}: reading batches repeat a lesson identity or plot")
            identities.add(lesson.id)
            plots.add(plot)
            lessons.append(lesson)
    return tuple(lessons)


def readings_for(stage_id: str) -> tuple[ReadingLesson, ...]:
    require_stage(stage_id)
    version = tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size)
                    for path in reading_paths(CONTENT_DIR, stage_id))
    return _readings(str(CONTENT_DIR), stage_id, version)


@lru_cache(maxsize=4)
def _source_listening(path: str, modified: int) -> SourceListeningDocument:
    return SourceListeningDocument.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _source_listening_parts(stage_id: str, topic) -> list[dict]:
    path = CONTENT_DIR / "study" / "source-listening.json"
    document = _source_listening(str(path), path.stat().st_mtime_ns)
    authored = next((lesson for lesson in document.lessons
                     if lesson.stage_id == stage_id and lesson.activity_id == topic.id), None)
    if authored is None:
        raise service.CurriculumError("this source has no authored sequential listening activity", 404)
    sections = authored.listening.sections
    for language in ("nl", "en"):
        original = " ".join(getattr(topic.listening.text, language).split())
        assembled = " ".join(" ".join(getattr(section.text, language) for section in sections).split())
        if assembled != original:
            raise ValueError("source listening sections must preserve the complete original script in order")
    descriptions = (("listen-gaps", copy("Luister en vul aan", "Listen and complete")),
                    ("listen-choose", copy("Luister en kies", "Listen and choose")),
                    ("listen-answer", copy("Luister en antwoord", "Listen and answer")))
    return [_part(key, title, text=_lines(section.text),
                  questions=[question.model_dump() for question in section.questions], instructions=copy(
                      "Lees eerst de vraag. Luister naar dit deel en antwoord terwijl je luistert. "
                      "Ga daarna naar het volgende deel van dezelfde opname.",
                      "Read the question first. Listen to this section and answer as you listen. "
                      "Then continue to the next section of the same recording."))
            for (key, title), section in zip(descriptions, sections, strict=True)]


@lru_cache(maxsize=32)
def _referenced_base_words(path: str, modified: int, wanted: tuple[str, ...]) -> dict[str, LibraryWord]:
    """Resolve a few explicit shared word IDs without constructing a story bank."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("stage_id") != Path(path).stem:
        raise ValueError("guided shared vocabulary does not match its stage")
    selected = {value["id"]: LibraryWord.model_validate(value) for value in data["vocabulary"]
                if value["id"] in wanted}
    if set(selected) != set(wanted):
        raise ValueError("guided source lesson refers to unknown shared vocabulary")
    return selected


def require_stage(stage_id: str):
    if stage_id not in STAGE_IDS:
        raise service.CurriculumError("learning stage not found", 404)


def catalogue(stage_id: str, skill: Skill, *, query: str = "", topic_group: str = "") -> dict:
    require_stage(stage_id)
    document, index = documents()
    mapped = index.stages.get(stage_id, {}).get(skill, {})
    groups = sorted({topic.group for topic in document.topics})
    items = []
    for topic in document.topics:
        if topic_group and topic.group != topic_group:
            continue
        if query and normalise(query) not in normalise(" ".join([topic.nl, topic.en, *topic.keywords])):
            continue
        sources = mapped.get(topic.id, [])
        items.append({"id": topic.id, "title": copy(topic.nl, topic.en), "group": topic.group,
                      "activity_count": len(sources), "available": bool(sources),
                      "availability_note": None if sources else copy(
                          "Voor dit niveau is dit onderwerp nog in voorbereiding.",
                          "This topic is still being prepared for this level.")})
    return {"stage_id": stage_id, "skill": skill, "groups": [{"id": group, "title": copy(*GROUPS.get(group, (group, group)))}
                                                               for group in groups],
            "topics": items, "total_topics": len(document.topics),
            "available_topics": sum(bool(mapped.get(topic.id)) for topic in document.topics)}


def _part(key: str, title: dict, *, prompt: dict | None = None, sample: dict | None = None,
          text: list[dict] | None = None, questions: list[dict] | None = None,
          instructions: dict | None = None, min_words: int = 1, max_words: int = 200) -> dict:
    guidance = copy(
        "Lees de tekst en beantwoord de vragen. Je kunt elke zin ook beluisteren.",
        "Read the text and answer the questions. You can also listen to each sentence.") if key == "read" else copy(
            "Probeer eerst zelf. Vraag daarna feedback en verbeter je antwoord.",
            "Try it yourself first. Then request feedback and improve your answer.")
    return {"id": key, "title": title, "prompt": prompt or title, "sample": sample,
            "text": text or [], "questions": questions or [],
            "instructions": instructions or guidance,
            "min_words": min_words, "max_words": max_words, "practice_questions": []}


def _questions(values) -> list[dict]:
    return [{"id": getattr(value, "id", "story-understand"), "kind": "choice",
             "prompt": bilingual(value.prompt), "options": [bilingual(option) for option in value.options],
             "answer_index": value.answer_index, "accepted_answers": [],
             "explanation": bilingual(value.explanation)} for value in values]


def _lines(value) -> list[dict]:
    # Existing localized paragraphs have different punctuation. Keep each
    # bilingual paragraph together instead of guessing translation alignment.
    nl = value.nl.split("\n\n")
    en = value.en.split("\n\n")
    if len(nl) == len(en):
        return [copy(left, right) for left, right in zip(nl, en, strict=True)]
    return [bilingual(value)]


def _word(word) -> dict:
    return {"id": word.id, "term": word.term, "part_of_speech": word.part_of_speech or "expression",
            "meaning": bilingual(word.meaning), "example": bilingual(word.example)}


def _preparation(stage_id: str, vocabulary_ids: list[str], source_text: str) -> dict:
    bank = library_for(stage_id)
    words = {word.id: word for word in bank.vocabulary}
    selected = [_word(words[key]) for key in vocabulary_ids if key in words][:12]
    # Rules appear only when an authored example occurs in the actual source.
    # A general stage rule is not automatically relevant to every story.
    normal = normalise(source_text)
    grammar = []
    for rule in service.stage_for(stage_id).grammar:
        examples = [bilingual(example) for example in rule.examples if normalise(example.nl) in normal]
        if examples:
            grammar.append({"title": bilingual(rule.title), "explanation": bilingual(rule.explanation),
                            "examples": examples[:3]})
    return {"words": selected, "grammar": grammar[:2]}


def _contextual_grammar(lines: list[dict], stage_id: str) -> list[dict]:
    """Explain an observable pattern, using the story's own exact sentence."""
    found = []
    for line in lines:
        text = line["nl"]
        if " want " in text.casefold():
            found.append({"title": copy("Een reden met want", "A reason with want"),
                          "explanation": copy("Na want volgt een gewone zin met onderwerp en persoonsvorm.",
                                              "After want, use ordinary subject–verb order."), "examples": [line]})
        elif " omdat " in text.casefold() and stage_id != "pre-a1":
            found.append({"title": copy("Een reden met omdat", "A reason with omdat"),
                          "explanation": copy("Omdat leidt een bijzin in; de werkwoorden staan achteraan in die bijzin.",
                                              "Omdat introduces a subordinate clause; its verbs go at the end."),
                          "examples": [line]})
        elif re.match(r"^(Ik|Je|U|Hij|Zij|We|Wij|[A-Z][a-z]+) "
                      r"(ben|bent|is|zijn|heb|heeft|had|was|werkt|woont|gaat|komt|maakt|staat|wil|kan|moet|doet|neemt)\b", text):
            found.append({"title": copy("De persoonsvorm op de tweede plaats", "The finite verb in second position"),
                          "explanation": copy("In deze hoofdzin staat de persoonsvorm op de tweede zinsplaats. "
                                              "Daarvoor staat één zinsdeel: het onderwerp of bijvoorbeeld een tijd of plaats.",
                                              "Here the finite verb occupies the second position in the main clause. "
                                              "One constituent comes first, such as the subject or a time or place expression."),
                          "examples": [line]})
        if len(found) == 2:
            break
    # Avoid displaying the same explanation twice just to fill a preparation pane.
    return list({rule["title"]["nl"]: rule for rule in found}.values())


@lru_cache(maxsize=4)
def _reading_map(path: str, version: tuple) -> ReadingMapDocument:
    return ReadingMapDocument.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _original_reading_grammar(stage: str, topic: str, story_id: str, lines: list[dict]) -> list[dict]:
    path = CONTENT_DIR / "study/reading-map.json"
    if not path.exists():
        return []
    stat = path.stat()
    document = _reading_map(str(path), (stat.st_mtime_ns, stat.st_size))
    mapping = next((item for item in document.mappings if item.stage_id == stage and item.story_id == story_id), None)
    if mapping is None:
        return []
    if mapping.topic_id != topic:
        raise ValueError("reading preparation must retain its mapped topic")
    exact = {(line["nl"], line["en"]) for line in lines}
    if any((example.nl, example.en) not in exact for rule in mapping.grammar for example in rule.examples):
        raise ValueError("reading grammar preparation must preserve an exact bilingual source line")
    return [rule.model_dump() for rule in mapping.grammar]


def _pack_preparation(stage_id: str, canonical, source) -> dict:
    text = " ".join(line.nl for line in source.lines)
    bank = library_for(stage_id)
    selected = []
    seen = set()
    for word in source.words:
        if word.minimum_stage in STAGE_IDS and STAGE_IDS.index(word.minimum_stage) > STAGE_IDS.index(stage_id):
            continue
        selected.append({"id": f"{source.id}-word-{len(selected)}", "term": word.term,
                         "part_of_speech": word.part_of_speech,
                         "meaning": copy(word.meaning.get("nl", word.term), word.meaning.get("en", word.term)),
                         "example": bilingual(word.example)})
        seen.add(normalise(word.term))
    matches = []
    for word in sorted(bank.vocabulary, key=lambda item: (not item.productive_core,
                                                         item.part_of_speech is None)):
        term = re.sub(r"^(de|het|een)\s+", "", word.term.casefold())
        if normalise(word.term) not in seen and re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE):
            matches.append(word)
    # Where the source supplies them, include different productive word
    # classes rather than filling every compact card with nouns alone.
    for part_of_speech in ("noun", "verb", "adjective"):
        match = next((word for word in matches if word.part_of_speech == part_of_speech), None)
        if match and normalise(match.term) not in seen and len(selected) < 8:
            selected.append(_word(match))
            seen.add(normalise(match.term))
    for word in matches:
        if len(selected) >= 5:
            break
        if normalise(word.term) not in seen:
            selected.append(_word(word))
            seen.add(normalise(word.term))
    # Topic vocabulary is authored and level-gated. It is supplementary to the
    # story words rather than a claim that every lemma occurs in this narrative.
    for word in canonical.vocabulary:
        if len(selected) >= 8:
            break
        if word.minimum_stage not in STAGE_IDS or STAGE_IDS.index(word.minimum_stage) > STAGE_IDS.index(stage_id):
            continue
        if normalise(word.term) in seen:
            continue
        selected.append({"id": f"{canonical.id}-word-{len(selected)}", "term": word.term,
                         "part_of_speech": word.part_of_speech,
                         "meaning": copy(word.meaning.get("nl", word.term), word.meaning.get("en", word.term)),
                         "example": bilingual(word.example)})
        seen.add(normalise(word.term))
    for word in matches:
        if len(selected) >= 8:
            break
        if normalise(word.term) not in seen:
            selected.append(_word(word))
            seen.add(normalise(word.term))
    grammar = [rule.model_dump() for rule in source.grammar]
    if not grammar:
        grammar = _contextual_grammar([bilingual(line) for line in source.lines], stage_id)
    return {"words": selected, "grammar": grammar}


def _reading_parts(stage_id: str, lines: list[dict], questions: list[dict]) -> list[dict]:
    low = STAGE_IDS.index(stage_id) < STAGE_IDS.index("b1")
    bound = 40 if stage_id == "pre-a1" else (120 if low else 350)
    if stage_id == "pre-a1":
        retell_prompt = copy(
            "Noem een persoon of ding uit het verhaal. Zeg of schrijf één korte zin.",
            "Name a person or thing from the story. Say or write one short sentence.")
    elif stage_id in ("pre-c1", "c1", "pre-c2", "c2"):
        retell_prompt = copy(
            "Geef een beknopte interpretatie van het verhaal. Maak onderscheid tussen wat de tekst expliciet "
            "zegt en wat je afleidt. Onderbouw je interpretatie met twee concrete details.",
            "Give a concise interpretation of the story. Distinguish what it explicitly states from what "
            "you infer. Support your interpretation with two specific details.")
    elif stage_id in ("pre-b2", "b2"):
        retell_prompt = copy(
            "Vat het verhaal samen. Vergelijk twee gebeurtenissen of standpunten en leg het verband ertussen uit.",
            "Summarise the story. Compare two events or viewpoints and explain how they relate.")
    elif stage_id in ("pre-b1", "b1"):
        retell_prompt = copy(
            "Vertel wat er gebeurt, in welke volgorde en waarom. Gebruik een belangrijk detail uit het verhaal.",
            "Explain what happens, in what order and why. Use an important detail from the story.")
    else:
        retell_prompt = copy("Wat gebeurt er in dit verhaal? Vertel het in je eigen woorden.",
                             "What happens in the story? Explain in your own words.")
    return [_part("read", copy("Lees het verhaal", "Read the story"), text=lines, questions=questions),
            _part("retell", copy("Vertel wat je begrijpt", "Explain what you understood"),
                  prompt=retell_prompt, max_words=bound)]


def _default_pack_parts(stage_id: str, canonical, source, skill: Skill) -> list[dict]:
    lines = [bilingual(line) for line in source.lines]
    low = STAGE_IDS.index(stage_id) < STAGE_IDS.index("b1")
    bound = 40 if stage_id == "pre-a1" else (120 if low else 350)
    questions = _questions(source.questions)
    if skill == "reading":
        return _reading_parts(stage_id, lines, questions)
    if skill == "speaking":
        if stage_id in ("pre-c1", "c1", "pre-c2", "c2"):
            describe_prompt = copy(
                "Vertel de situatie na voor iemand die de tekst niet kent. Maak de verbanden duidelijk "
                "en pas je woordkeuze aan een professionele gesprekspartner aan.",
                "Explain the situation to someone unfamiliar with the text. Make its connections clear "
                "and adapt your wording for a professional listener.")
        elif stage_id in ("pre-b2", "b2"):
            describe_prompt = copy(
                "Beschrijf de situatie samenhangend. Leg uit welk probleem of verschil er is en geef een reden.",
                "Describe the situation coherently. Explain a problem or difference and give a reason.")
        elif stage_id in ("pre-b1", "b1"):
            describe_prompt = copy(
                "Vertel het verhaal samenhangend na. Leg uit wat er eerst en daarna gebeurt.",
                "Retell the story as a connected account. Explain what happens first and next.")
        else:
            describe_prompt = copy("Vertel het verhaal na. Beschrijf wie of wat belangrijk is.",
                                   "Retell the story. Describe who or what matters.")
        warmup = _part("short-answers", copy("Korte vragen", "Short questions"),
                       prompt=copy("Wat gebeurt er aan het begin van dit verhaal?",
                                   "What happens at the beginning of this story?"),
                       sample=lines[0], max_words=min(50, bound))
        warmup["practice_questions"] = [
            {"id": "opening", "prompt": warmup["prompt"], "sample": lines[0]},
            {"id": "next", "prompt": copy("Wat gebeurt er daarna?", "What happens next?"), "sample": lines[1]},
            *[{"id": f"topic-{index}", "prompt": bilingual(question),
               "sample": (bilingual(canonical.short_question_samples[index - 1])
                          if len(canonical.short_question_samples) >= index else None)}
              for index, question in enumerate(canonical.short_questions, 1)],
        ]
        if stage_id == "pre-a1":
            # Foundation lessons practise recognisable concrete information,
            # not an abstract taxonomy question simply because it exists.
            warmup["practice_questions"] = [
                {"id": f"source-{index}", "prompt": bilingual(question.prompt),
                 "sample": bilingual(question.options[question.answer_index])}
                for index, question in enumerate(source.questions[:2], 1)]
            warmup["prompt"] = warmup["practice_questions"][0]["prompt"]
            warmup["sample"] = warmup["practice_questions"][0]["sample"]
        elif canonical.short_questions:
            warmup["practice_questions"] = (warmup["practice_questions"][2:]
                                            + warmup["practice_questions"][:2])
            warmup["prompt"] = warmup["practice_questions"][0]["prompt"]
            warmup["sample"] = warmup["practice_questions"][0]["sample"]
        description = _part("describe", copy("Beschrijf en vertel", "Describe and tell"),
                            prompt=describe_prompt,
                            sample=copy(" ".join(line["nl"] for line in lines[:3]),
                                        " ".join(line["en"] for line in lines[:3])), max_words=bound)
        discussion = _part("discuss", copy("Praat verder", "Continue the discussion"),
                           prompt=copy("Welke zin vind je belangrijk? Lees die voor en zeg waarom.",
                                       "Which sentence matters to you? Read it aloud and say why.") if low else copy(
                                           "Welke zin vat voor jou de kern van het verhaal samen? "
                                           "Onderbouw je interpretatie met een tweede zin uit de tekst.",
                                           "Which sentence captures the story's main point for you? "
                                           "Support your interpretation with a second sentence from the text."),
                           sample=copy(f"Ik vind deze zin belangrijk: {lines[0]['nl']} "
                                       "Deze zin helpt mij om het verhaal te begrijpen.",
                                       f"This sentence matters to me: {lines[0]['en']} "
                                       "It helps me understand the story.") if low else copy(
                                           f"Voor mij is de kern: {lines[-1]['nl']} "
                                           f"Die zin sluit het verhaal af. Het begin is: {lines[0]['nl']}",
                                           f"For me, the main point is: {lines[-1]['en']} "
                                           f"It closes the story. The beginning is: {lines[0]['en']}"), max_words=bound)
        if stage_id == "pre-a1":
            description["prompt"] = copy("Zeg twee korte zinnen over de situatie. Je mag het voorbeeld gebruiken.",
                                          "Say two short sentences about the situation. You may use the example.")
            description["sample"] = copy(" ".join(line["nl"] for line in lines[:2]),
                                          " ".join(line["en"] for line in lines[:2]))
            last_question = source.questions[-1]
            discussion["prompt"] = bilingual(last_question.prompt)
            discussion["sample"] = bilingual(last_question.options[last_question.answer_index])
        return [warmup, description, discussion]
    if skill == "writing":
        short = _part("write-short", copy("Schrijf korte zinnen", "Write short sentences"),
                      prompt=copy("Schrijf twee zinnen over het begin van dit verhaal.",
                                  "Write two sentences about the beginning of this story."),
                      sample=copy(" ".join(line["nl"] for line in lines[:2]),
                                  " ".join(line["en"] for line in lines[:2])), max_words=min(70, bound))
        extended = _part("write-extended", copy("Schrijf je eigen versie", "Write your own version"),
                         prompt=copy("Vertel in een kort bericht wat er gebeurt in het verhaal.",
                                     "Write a short message explaining what happens in the story.") if low else copy(
                                         "Schrijf een samenhangende samenvatting van het verhaal. "
                                         "Maak duidelijk hoe het begin en het einde met elkaar verbonden zijn.",
                                         "Write a connected account of the story. "
                                         "Make clear how its beginning and ending relate to each other."),
                         sample=copy(" ".join(line["nl"] for line in lines),
                                     " ".join(line["en"] for line in lines)), max_words=bound)
        return [short, extended]
    # A single authored narrative is split into consecutive sections. The
    # three recordings and their questions follow that narrative's chronology.
    cut1, cut2 = max(2, len(lines) // 3), max(4, 2 * len(lines) // 3)
    opening, middle, ending = lines[:cut1], lines[cut1:cut2], lines[cut2:]
    first = opening[0]
    tokens = re.findall(r"(?<!\w)[A-Za-zÀ-ÿ]+(?!\w)", first["nl"])
    target = next((word for word in reversed(tokens) if len(word) >= 3), tokens[-1])
    blank = re.sub(rf"(?<!\w){re.escape(target)}(?!\w)", "_____", first["nl"], count=1)
    gap = {"id": f"{source.id}-listen-gap", "kind": "gap", "prompt": copy(blank, "Complete the missing Dutch word."),
           "options": [], "answer_index": None, "accepted_answers": [target], "explanation": first}
    choices = [{"nl": line["nl"], "en": line["en"]} for line in (middle[0], opening[0], ending[-1])]
    correct_index = hashlib.sha256(source.id.encode()).digest()[0] % len(choices)
    choices = choices[-correct_index:] + choices[:-correct_index] if correct_index else choices
    choose = {"id": f"{source.id}-listen-choice", "kind": "choice",
              "prompt": copy("Wat gebeurt er in dit deel van het verhaal?", "What happens in this section of the story?"),
              "options": choices, "answer_index": correct_index, "accepted_answers": [], "explanation": middle[0]}
    last = ending[-1]
    short_answer = {"id": f"{source.id}-listen-answer", "kind": "short",
                    "prompt": copy("Schrijf de laatste zin die je hoort.", "Write the final sentence you hear."),
                    "options": [], "answer_index": None, "accepted_answers": [last["nl"]], "explanation": last}
    closing_question = source.questions[-1]
    closing_answer = closing_question.options[closing_question.answer_index]
    if normalise(closing_answer.nl) in normalise(" ".join(line["nl"] for line in ending)):
        short_answer.update({"prompt": bilingual(closing_question.prompt),
                             "accepted_answers": [closing_answer.nl],
                             "explanation": bilingual(closing_question.explanation)})
    return [_part("listen-gaps", copy("Luister en vul aan", "Listen and complete"), text=opening, questions=[gap]),
            _part("listen-choose", copy("Luister en kies", "Listen and choose"), text=middle, questions=[choose]),
            _part("listen-answer", copy("Luister en antwoord", "Listen and answer"), text=ending,
                  questions=[short_answer], instructions=copy(
                      "Antwoord in het Nederlands. De snelle controle vergelijkt met een referentieantwoord; "
                      "een andere juiste formulering kan extra beoordeling nodig hebben.",
                      "Answer in Dutch. The quick check compares a reference answer; "
                      "another correct wording may need further review."))]


def _pack_parts(stage_id: str, canonical, source, skill: Skill) -> list[dict]:
    """Authored tasks override the baseline; the baseline is never a silent replacement."""
    parts = _default_pack_parts(stage_id, canonical, source, skill)
    if skill in ("speaking", "writing"):
        parts = _purposeful_parts(stage_id, canonical, source, skill, parts)
    if skill == "speaking" and source.speaking:
        override = source.speaking
        if override.short_questions:
            warmup = parts[0]
            warmup["practice_questions"] = [
                {"id": f"authored-{index}", "prompt": bilingual(question.prompt), "sample": bilingual(question.sample)}
                for index, question in enumerate(override.short_questions, 1)]
            warmup["prompt"] = warmup["practice_questions"][0]["prompt"]
            warmup["sample"] = warmup["practice_questions"][0]["sample"]
        mappings = ((1, override.description), (2, override.discussion))
    elif skill == "writing" and source.writing:
        mappings = ((0, source.writing.short), (1, source.writing.extended))
    elif skill == "listening" and source.listening:
        for part, section in zip(parts, source.listening.sections, strict=True):
            part["text"] = _lines(section.text)
            part["questions"] = [question.model_dump() for question in section.questions]
        return parts
    else:
        return _sample_bounds(parts)
    for index, task in mappings:
        if task is not None:
            parts[index].update({"prompt": bilingual(task.prompt), "sample": bilingual(task.sample),
                                 "min_words": task.min_words, "max_words": task.max_words})
    return _sample_bounds(parts)


def _sample_bounds(parts: list[dict]) -> list[dict]:
    # Models are examples, never ungrammatical word-truncated snippets. When a
    # short source needs a slightly longer greeting/closing, show an honest
    # advisory range that can actually contain the supplied Dutch example.
    for part in parts:
        if part.get("sample"):
            count = service.word_count(part["sample"]["nl"])
            part["max_words"] = max(part["max_words"], count)
    return parts


def _purposeful_parts(stage_id: str, canonical, source, skill: Skill, parts: list[dict]) -> list[dict]:
    """Give baseline productive tasks a recipient and a useful communication goal.

    Examples quote authored situation facts rather than manufacturing an
    outcome, conjugation or personal experience. Specialist authored overrides
    remain the primary route for richer professional and academic provision.
    """
    audiences = {
        "work": ("een collega", "a colleague"), "study": ("een medestudent", "a fellow student"),
        "services": ("een medewerker aan het onthaal", "a reception desk employee"),
        "environment": ("een buurtbewoner", "a neighbour"), "places": ("een medereiziger", "a fellow traveller"),
        "culture": ("een bezoeker", "a visitor"), "leisure": ("een teamgenoot", "a teammate"),
        "money": ("een huisgenoot", "a housemate"), "digital": ("een collega", "a colleague"),
    }
    recipient_nl, recipient_en = audiences.get(canonical.group, ("een vriend", "a friend"))
    lines = [bilingual(line) for line in source.lines]
    whole = copy(" ".join(line["nl"] for line in lines), " ".join(line["en"] for line in lines))
    q = source.questions[0]
    answer = q.options[q.answer_index]
    anchor = next((line for line in lines if normalise(answer.nl).strip(".!?")
                   in normalise(line["nl"])), bilingual(answer))
    foundation = stage_id == "pre-a1"
    beginner = stage_id in ("pre-a1", "a1")
    routine = stage_id in ("pre-a2", "a2")
    independent = stage_id in ("pre-b1", "b1")
    if skill == "speaking":
        if beginner:
            questions = [{"id": f"source-{index}", "prompt": bilingual(question.prompt),
                          "sample": bilingual(question.options[question.answer_index])}
                         for index, question in enumerate(source.questions[:2], 1)]
            parts[0].update({"prompt": questions[0]["prompt"], "sample": questions[0]["sample"],
                             "practice_questions": questions})
        if foundation:
            parts[1].update({"prompt": copy(
                "Je praat met iemand uit de situatie. Zeg één naam, woord of korte zin die past.",
                "You are talking to someone in this situation. Say one suitable name, word or short sentence."),
                             "sample": anchor})
            return parts
        parts[1]["prompt"] = copy(
            f"Je praat met {recipient_nl}. Beschrijf de persoon, plaats of activiteit uit deze situatie. "
            + ("Gebruik korte zinnen: wie, wat en waar?" if beginner else
               "Leg uit wat er gebeurt en noem twee belangrijke details." if routine else
               "Vertel samenhangend wat belangrijk is, licht een reden toe en vraag of de ander je begrijpt." if independent else
               "Kies relevante details, maak verbanden duidelijk en pas je toon aan je gesprekspartner aan."),
            f"You are talking to {recipient_en}. Describe the person, place or activity in this situation. "
            + ("Use short sentences: who, what and where?" if beginner else
               "Explain what happens and include two important details." if routine else
               "Give a connected account, explain a reason and check that the listener understands." if independent else
               "Select relevant details, make connections clear and adapt your tone to your listener."))
        parts[1]["sample"] = copy(f"Dag. {whole['nl']}", f"Hello. {whole['en']}")
        if beginner:
            parts[2]["prompt"] = copy("Wat wil je nog weten over de situatie? Stel één korte vraag.",
                                       "What else would you like to know about the situation? Ask one short question.")
            parts[2]["sample"] = bilingual(source.questions[-1].prompt)
        elif routine:
            parts[2]["prompt"] = copy(
                "Wat zou je eerst doen in deze situatie? Geef één idee en een eenvoudige reden.",
                "What would you do first in this situation? Give one idea and a simple reason.")
            parts[2]["sample"] = copy(
                f"Ik vraag eerst: {source.questions[-1].prompt.nl} Dan weet ik meer over de situatie.",
                f"First I ask: {source.questions[-1].prompt.en} Then I know more about the situation.")
        elif independent:
            parts[2]["prompt"] = copy(
                "Wat zou jij doen in deze situatie? Licht je keuze toe en stel een passende vervolgvraag.",
                "What would you do in this situation? Explain your choice and ask an appropriate follow-up question.")
            parts[2]["sample"] = copy(
                f"Ik zou eerst de situatie bespreken. Dit detail vind ik belangrijk: {lines[-1]['nl']} "
                f"Daarom zou ik vragen: {source.questions[-1].prompt.nl}",
                f"I would discuss the situation first. This detail matters to me: {lines[-1]['en']} "
                f"That is why I would ask: {source.questions[-1].prompt.en}")
        else:
            parts[2]["prompt"] = copy(
                f"Bespreek met {recipient_nl} twee manieren om naar deze situatie te kijken. "
                "Onderbouw je standpunt met details en leg uit welke informatie je nog nodig hebt.",
                f"Discuss two ways of looking at this situation with {recipient_en}. "
                "Support your position with details and explain what further information you need.")
            parts[2]["sample"] = copy(
                f"Enerzijds lees ik: ‘{lines[0]['nl']}’ Anderzijds staat er: ‘{lines[-1]['nl']}’ "
                "Ik zou die gegevens samen bekijken voordat ik een conclusie trek. "
                f"Een vraag die daarbij helpt, is: {source.questions[-1].prompt.nl}",
                f"On the one hand, I read: ‘{lines[0]['en']}’ On the other, the text says: ‘{lines[-1]['en']}’ "
                "I would consider those details together before reaching a conclusion. "
                f"A useful question would be: {source.questions[-1].prompt.en}")
        return parts
    parts[0].update({"prompt": copy(
        f"{q.prompt.nl} " + ("Schrijf een woord of een korte zin." if foundation else
                            "Antwoord met een volledige korte zin." if beginner else
                            "Schrijf een kort, duidelijk antwoord met een relevant detail." if routine else
                            "Schrijf een beknopt antwoord en kies de informatie die de lezer nodig heeft."),
        f"{q.prompt.en} " + ("Write a word or a short sentence." if foundation else
                            "Answer in one complete short sentence." if beginner else
                            "Write a brief, clear answer with a relevant detail." if routine else
                            "Write a concise answer and select the information your reader needs.")),
                     "sample": bilingual(answer) if foundation else anchor})
    if foundation:
        parts[1].update({"prompt": copy(
            "Je maakt een kort bericht bij de situatie. Schrijf een naam of woord en één korte zin.",
            "Make a short message for this situation. Write a name or word and one short sentence."),
                         "sample": copy(f"Dag. {anchor['nl']}", f"Hello. {anchor['en']}")})
        return parts
    formal = canonical.group == "services"
    greeting_nl, ending_nl = ("Beste,", "Met vriendelijke groeten,") if formal else ("Dag,", "Groetjes,")
    question_nl = "Wat denkt u daarvan?" if formal else "Wat denk jij daarvan?"
    if beginner:
        task_nl = "Schrijf een kort bericht. Vertel wie, wat en waar. Sluit af met een groet."
        task_en = "Write a short message. Explain who, what and where. End with a greeting."
    elif routine:
        task_nl = "Schrijf een korte e-mail. Leg de situatie uit, noem een belangrijk detail en vraag om een reactie."
        task_en = "Write a short email. Explain the situation, include an important detail and ask for a reply."
    elif independent:
        task_nl = ("Schrijf een samenhangende e-mail. Leg de situatie en een reden of gevolg uit. "
                   "Stel aan het einde een passende vraag.")
        task_en = ("Write a connected email. Explain the situation and a reason or consequence. "
                   "End with an appropriate question.")
    else:
        task_nl = ("Schrijf een gemotiveerde reactie. Maak duidelijk welke feiten je gebruikt, licht je standpunt toe "
                   "en bespreek welke informatie nog ontbreekt.")
        task_en = ("Write a reasoned response. Identify the facts you use, explain your position "
                   "and discuss what information is still missing.")
    parts[1]["prompt"] = copy(f"Je schrijft aan {recipient_nl}. {task_nl}",
                              f"You are writing to {recipient_en}. {task_en}")
    extra_nl = (f"\nVoor mij is dit detail belangrijk: ‘{lines[-1]['nl']}’ "
                "Ik zou de informatie eerst met de betrokkenen bespreken voordat ik een standpunt inneem.") if not (
                    beginner or routine or independent) else ""
    extra_en = (f"\nThis detail matters to me: ‘{lines[-1]['en']}’ "
                "I would discuss the information with those involved before taking a position.") if not (
                    beginner or routine or independent) else ""
    parts[1]["sample"] = copy(f"{greeting_nl}\n\n{whole['nl']}{extra_nl}\n\n{question_nl}\n\n{ending_nl}",
                              f"Hello,\n\n{whole['en']}{extra_en}\n\nWhat do you think about this?\n\nKind regards,")
    return parts


def _practice_parts(stage_id: str, topic, skill: Skill, *, source_words: dict | None = None) -> list[dict]:
    if skill == "reading":
        return [_part("read", copy("Lees en begrijp", "Read and understand"),
                      text=_lines(topic.reading.text), questions=_questions(topic.reading.questions)),
                _part("retell", copy("Vertel wat je begrijpt", "Explain what you understood"),
                      prompt=copy("Vertel in je eigen woorden waarover de tekst gaat. Noem een belangrijk detail.",
                                  "Explain the text in your own words. Include an important detail."),
                      min_words=1, max_words=200)]
    if skill == "listening":
        return _source_listening_parts(stage_id, topic)
    task = getattr(topic, skill)
    early = STAGE_IDS.index(stage_id) < STAGE_IDS.index("b1")
    if skill == "speaking":
        short_prompt = bilingual(task.criteria[0])
        followup = copy(
            "Kies een nuttige zin uit het voorbeeld. Zeg de zin en leg kort uit waarom die helpt.",
            "Choose a useful sentence from the example. Say it and briefly explain why it helps.") if early else copy(
                "Welke aanpak uit het voorbeeld zou je gebruiken? Licht je keuze toe en bespreek een alternatief.",
                "Which approach from the example would you use? Explain your choice and discuss an alternative.")
        sample_nl = re.split(r"(?<=[.!?])\s+", task.sample.nl)[0]
        sample_en = re.split(r"(?<=[.!?])\s+", task.sample.en)[0]
        followup_sample = copy(
            f"Een nuttige zin is: {sample_nl} Zo maak ik duidelijk wat ik bedoel.",
            f"A useful sentence is: {sample_en} It helps me make my meaning clear.") if early else copy(
                f"Ik zou deze aanpak gebruiken: {sample_nl} "
                "Als alternatief zou ik eerst vragen welke andere mogelijkheden er zijn.",
                f"I would use this approach: {sample_en} "
                "Alternatively, I would first ask what other options are available.")
        if stage_id == "pre-a1":
            followup = bilingual(task.criteria[-1])
            followup_sample = bilingual(task.sample)
        return [_part("short-answers", copy("Korte antwoorden", "Short answers"), prompt=short_prompt,
                      sample=bilingual(task.sample), max_words=min(40, task.max_words)),
                _part("describe", copy("Beschrijf de situatie", "Describe the situation"),
                      prompt=bilingual(task.prompt), sample=bilingual(task.sample),
                      min_words=task.min_words, max_words=task.max_words),
                _part("discuss", copy("Praat verder", "Continue the conversation"),
                      prompt=followup, sample=followup_sample, max_words=task.max_words)]
    return [_part("write-short", copy("Bouw je zinnen op", "Build your sentences"),
                  prompt=bilingual(task.criteria[0]), sample=bilingual(task.sample), max_words=min(60, task.max_words)),
            _part("write-extended", copy("Schrijf je bericht", "Write your response"),
                  prompt=bilingual(task.prompt), sample=bilingual(task.sample),
                  min_words=task.min_words, max_words=task.max_words)]


def lesson(stage_id: str, topic_id: str, skill: Skill, *, activity_id: str | None = None,
           include_answers: bool = False) -> dict:
    require_stage(stage_id)
    document, index = documents()
    canonical = next((topic for topic in document.topics if topic.id == topic_id), None)
    if canonical is None:
        raise service.CurriculumError("study topic not found", 404)
    sources = index.stages.get(stage_id, {}).get(skill, {}).get(topic_id, [])
    if not sources:
        raise service.CurriculumError("this topic has no authored activity for this stage and skill", 404)
    selected = next((source for source in sources if source.id == activity_id), None) if activity_id else sources[0]
    if selected is None:
        raise service.CurriculumError("study activity not found in this topic", 404)
    activities = []
    # The guided index is pack-first. Do not parse a complete legacy topic
    # bank, including its four-skill exercises, merely to open one new story.
    needs_practice = any(source.source == "practice" for source in sources)
    narrow_source = needs_practice and all(source.source != "practice" or "-t-source-" in source.id
                                          for source in sources)
    source_words = None
    if narrow_source:
        path = CONTENT_DIR / "source-lessons" / f"{stage_id}.json"
        data = supplements._read(str(path), (path.stat().st_mtime_ns, path.stat().st_size))
        topic_bank = {value["id"]: PracticeTopic.model_validate(value) for value in data["topics"]}
        source_words = {value["id"]: LibraryWord.model_validate(value) for value in data["vocabulary"]}
        missing = tuple(sorted({key for topic in topic_bank.values() for key in topic.vocabulary_ids} - set(source_words)))
        if missing:
            shared = CONTENT_DIR / "library" / f"{stage_id}.json"
            source_words.update(_referenced_base_words(str(shared), shared.stat().st_mtime_ns, missing))
    else:
        topic_bank = ({topic.id: topic for topic in topics_for(stage_id).topics} if needs_practice else {})
    stories = ({story.id: story for story in library_for(stage_id).stories}
               if any(source.source == "story" for source in sources) else {})
    pack = pack_for(stage_id)
    authored = {item.id: item for item in pack.lessons} if pack else {}
    readings = ({item.id: item for item in readings_for(stage_id)}
                if any(source.source == "reading" for source in sources) else {})
    for source in sources:
        item = (stories.get(source.id) if source.source == "story" else
                authored.get(source.id) if source.source == "pack" else
                readings.get(source.id) if source.source == "reading" else topic_bank.get(source.id))
        if item is None:
            raise ValueError("guided source reference does not resolve")
        activities.append({"id": source.id, "title": bilingual(item.title)})
    if selected.source == "pack":
        source = authored[selected.id]
        if source.topic_id != topic_id:
            raise ValueError("guided pack was assigned to another topic")
        parts = _pack_parts(stage_id, canonical, source, skill)
        source_text = " ".join(line.nl for line in source.lines)
        context_lines = [bilingual(line) for line in source.lines]
        preparation = _pack_preparation(stage_id, canonical, source)
    elif selected.source == "reading":
        source = readings[selected.id]
        if skill != "reading" or source.topic_id != topic_id:
            raise ValueError("an original reading must retain its skill and authored topic")
        context_lines = [bilingual(line) for line in source.lines]
        parts = _reading_parts(stage_id, context_lines, _questions(source.questions))
        source_text = " ".join(line.nl for line in source.lines)
        preparation = {"words": [
            {"id": f"{source.id}-word-{index}", "term": word.term, "part_of_speech": word.part_of_speech,
             "meaning": bilingual(word.meaning), "example": bilingual(word.example)}
            for index, word in enumerate(source.words, 1)],
            "grammar": [rule.model_dump() for rule in source.grammar]}
    elif selected.source == "story":
        if skill != "reading" or selected.id not in eligible_story_ids(stage_id):
            raise ValueError("guided stories require eligible reading sources")
        source = stories[selected.id]
        text = [bilingual(line) for line in source.lines or []]
        questions = _questions([source.question])
        questions[0]["id"] = f"{source.id}-understand"
        parts = _reading_parts(stage_id, text, questions)
        source_text = " ".join(line["nl"] for line in text)
        context_lines = text
    elif selected.source == "practice":
        source = topic_bank[selected.id]
        parts = _practice_parts(stage_id, source, skill, source_words=source_words)
        source_text = (getattr(source, skill).text.nl if skill in ("reading", "listening")
                       else getattr(source, skill).prompt.nl)
        context_lines = _lines(source.reading.text)
    else:
        raise service.CurriculumError("this authored study pack is not available yet", 404)
    parts = _sample_bounds(parts)
    for part in parts:
        for question in part["questions"]:
            CheckQuestion.model_validate(question)
            if not include_answers:
                for key in ("answer_index", "accepted_answers", "explanation"):
                    question.pop(key, None)
    if selected.source not in {"pack", "reading"}:
        preparation = ({"words": [_word(source_words[key]) for key in source.vocabulary_ids if key in source_words],
                        "grammar": _contextual_grammar(_lines(source.reading.text), stage_id)}
                       if source_words is not None else _preparation(stage_id, source.vocabulary_ids, source_text))
        if selected.source == "story":
            authored_grammar = _original_reading_grammar(stage_id, topic_id, selected.id, context_lines)
            preparation["grammar"] = (authored_grammar or preparation["grammar"]
                                      or _contextual_grammar(context_lines, stage_id))
    return {"stage_id": stage_id, "topic_id": topic_id, "skill": skill,
            "title": bilingual(source.title), "topic_title": copy(canonical.nl, canonical.en),
            "review_status": "unreviewed", "preparation": preparation, "activities": activities,
            "activity_id": selected.id, "parts": parts,
            "context": {"title": bilingual(source.title), "text": context_lines},
            "policy": {"ephemeral": True, "pronunciation_assessed": False,
                       "recognized_certificate": False, "audio_locale": "nl-BE"}}
