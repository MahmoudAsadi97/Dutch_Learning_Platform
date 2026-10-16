"""Build original connected units without padding inventories with plot variants.

The requested 200 stories per stage is an editorial target, not a claim made by
this builder. Each accepted unit has its own plot and parallel authored lines.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("nl", "en", "fa")
CATEGORY = {"nl": "Verhaal naar gesprek", "en": "Story into conversation", "fa": "از داستان تا گفت‌وگو"}


def tr(value: str) -> dict[str, str]:
    parts = value.split("|")
    if len(parts) != 3 or any(not part.strip() for part in parts):
        raise ValueError("unit text needs Dutch, English and Persian")
    return dict(zip(LANGS, (part.strip() for part in parts), strict=True))


def lemma(value: str) -> str:
    return re.sub(r"^(de|het)\s+", "", value.casefold().strip())


def question(identifier: str, value: tuple, index: int) -> dict:
    prompt, answer, distractor, explanation = map(tr, value)
    position = index % 2
    return {"id": identifier, "prompt": prompt,
            "options": [answer, distractor] if position == 0 else [distractor, answer],
            "answer_index": position, "explanation": explanation}


def productive(unit: dict, skill: str) -> dict:
    low, high = unit[f"{skill}_bounds"]
    sample = tr(unit["spoken_sample" if skill == "speaking" else "written_sample"])
    count = len(sample["nl"].split())
    if not low <= count <= high:
        raise ValueError(f"{unit['id']} {skill} sample length {count} outside {low}..{high}")
    return {"prompt": tr(unit[skill]), "sample": sample, "min_words": low, "max_words": high,
            "criteria": [tr(item) for item in unit.get(f"{skill}_criteria", unit["criteria"])]}


def build(root: Path = ROOT, units: list[dict] | None = None) -> dict:
    if units is None:
        from scripts.content_build.learning_units_lower import UNITS as lower
        from scripts.content_build.learning_units_lower_extra import UNITS as extra
        from scripts.content_build.learning_units_upper import UNITS as upper
        units = [*lower, *extra, *upper]
    stages = json.loads((root / "content/alignment/learning-design.json").read_text())["stages"]
    known = {stage["id"] for stage in stages}
    grouped = defaultdict(list)
    ids = set()
    narratives = set()
    for unit in units:
        if unit["stage"] not in known or not re.fullmatch(r"[a-z0-9-]{1,35}", unit["id"]):
            raise ValueError("unit needs a known stage and stable short slug")
        if unit["id"] in ids:
            raise ValueError("unit slugs must be globally distinct")
        ids.add(unit["id"])
        lines = [tr(line) for line in unit["lines"]]
        if not 8 <= len(lines) <= 12:
            raise ValueError("a narrative needs 8–12 authored lines")
        text = " ".join(line["nl"] for line in lines)
        if text.casefold() in narratives:
            raise ValueError("cross-stage story reuse is not a new story")
        narratives.add(text.casefold())
        grouped[unit["stage"]].append(unit)
    packs = {}
    for stage, values in grouped.items():
        existing = {}
        for folder in ("library", "source-lessons"):
            path = root / f"content/{folder}/{stage}.json"
            if path.exists():
                existing.update({lemma(w["term"]): w["id"] for w in json.loads(path.read_text())["vocabulary"]})
        pack = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed",
                "vocabulary": [], "stories": [], "topics": [], "grammar_extensions": []}
        for unit in values:
            slug = unit["id"]
            story_id, topic_id = f"{stage}-s-unit-{slug}", f"{stage}-t-unit-{slug}"
            targets = []
            classes = unit["word_classes"]
            if len(classes) != len(unit["words"]):
                raise ValueError("each target needs its authored word class")
            for i, (term, meaning, example) in enumerate(unit["words"], 1):
                key = lemma(term)
                if key not in existing:
                    existing[key] = f"{stage}-unit-{slug}-v{i}"
                    pack["vocabulary"].append({"id": existing[key], "term": term, "topic": CATEGORY,
                                              "meaning": tr(meaning), "example": tr(example),
                                              "part_of_speech": classes[i - 1]})
                targets.append(existing[key])
            if len(set(targets)) != len(targets):
                raise ValueError("duplicate unit vocabulary target")
            lines = list(map(tr, unit["lines"]))
            halfway = len(lines) // 2
            paragraphs = [{lang: " ".join(line[lang] for line in section) for lang in LANGS}
                          for section in (lines[:halfway], lines[halfway:])]
            reading = {"text": {lang: "\n\n".join(p[lang] for p in paragraphs) for lang in LANGS},
                       "questions": [question(f"{topic_id}-r{i}", q, i) for i, q in enumerate(unit["reading_q"], 1)]}
            listening = {"text": tr(unit["listening"]),
                         "questions": [question(f"{topic_id}-l{i}", q, i) for i, q in enumerate(unit["listening_q"], 1)]}
            pack["topics"].append({"id": topic_id, "title": tr(unit["title"]), "category": CATEGORY,
                "objectives": [tr(unit["focus"])], "language_focus": tr(unit["focus"]),
                "vocabulary_ids": targets, "reading": reading, "listening": listening,
                "speaking": productive(unit, "speaking"), "writing": productive(unit, "writing")})
            story_q = dict(reading["questions"][0]); story_q.pop("id")
            pack["stories"].append({"id": story_id, "title": tr(unit["title"]), "topic": CATEGORY,
                "genre": tr(unit["genre"]),
                "lines": lines, "paragraphs": paragraphs, "topic_id": topic_id,
                "vocabulary_ids": targets, "question": story_q})
        packs[stage] = pack
    # Use the runtime contracts before any file is replaced, including audio bounds,
    # translated answer choices and task samples. Counts alone cannot validate a pack.
    from dlp.domains.curriculum.library import LibraryStory, LibraryWord
    from dlp.domains.curriculum.topics import PracticeTopic

    for pack in packs.values():
        for value in pack["vocabulary"]:
            LibraryWord.model_validate(value)
        for value in pack["stories"]:
            LibraryStory.model_validate(value)
        for value in pack["topics"]:
            PracticeTopic.model_validate(value)
    for stage, pack in packs.items():
        path = root / f"content/learning-units/{stage}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return packs


if __name__ == "__main__":
    result = build()
    for stage, pack in result.items():
        print(f"{stage}: {len(pack['stories'])} connected stories, {len(pack['topics']) * 4} skill activities")
