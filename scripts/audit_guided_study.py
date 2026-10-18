"""Validate guided topic packs and regenerate their source index on request.

This checks coverage, references, translations and exact repetition structurally.
It cannot certify CEFR difficulty, natural language, pronunciation or translation
accuracy. Dutch/English review remains a separate, recorded editorial step.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

STAGES = (
    "pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1", "pre-b2", "b2",
    "pre-c1", "c1", "pre-c2", "c2",
)
SKILLS = ("reading", "listening", "speaking", "writing")
SUPPLEMENTS = ("source-lessons", "learning-units", "reading-library")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def localized(value: Any, location: str) -> None:
    if not isinstance(value, dict) or any(
        not isinstance(value.get(lang), str) or not value[lang].strip()
        for lang in ("nl", "en")
    ):
        raise ValueError(f"{location}: nonblank Dutch and English copy required")
    if "fa" in value:
        raise ValueError(f"{location}: Persian copy is outside this guided course")


def normalized(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def taxonomy(content: Path) -> list[dict]:
    data = read(content / "study" / "topics.json")
    if data.get("schema_version") != 1 or data.get("language_variety") != "nl-BE":
        raise ValueError("unsupported guided topic catalogue")
    topics = data.get("topics", [])
    if len(topics) != 100 or len({topic["id"] for topic in topics}) != 100:
        raise ValueError("the learner's 100 distinct canonical topics are required")
    for topic in topics:
        slug = topic["id"]
        if not re.fullmatch(r"[a-z]+(?:-[a-z]+)*", slug):
            raise ValueError(f"invalid canonical topic ID: {slug}")
        localized({"nl": topic.get("nl"), "en": topic.get("en")}, slug)
        if not topic.get("keywords") or not topic.get("group"):
            raise ValueError(f"{slug}: search keywords and a topic group required")
        if topic.get("review_status") != "unreviewed":
            raise ValueError(f"{slug}: approval requires a separate editorial record")
        kinds = Counter()
        for word in topic.get("vocabulary", []):
            if not word.get("term") or not word.get("meaning", {}).get("en"):
                raise ValueError(f"{slug}: vocabulary needs a term and English gloss")
            localized(word["meaning"], f"{slug}/{word['term']}/definition")
            localized(word.get("example"), f"{slug}/{word.get('term')}")
            if word.get("minimum_stage") not in STAGES:
                raise ValueError(f"{slug}: vocabulary has an unknown starting stage")
            kinds[word.get("part_of_speech")] += 1
        if not kinds["noun"] or not kinds["verb"]:
            raise ValueError(f"{slug}: preparation must include a noun and a verb")
        if len(topic.get("short_questions", [])) < 2:
            raise ValueError(f"{slug}: two topical warm-up questions required")
        for question in topic["short_questions"]:
            localized(question, f"{slug}/short-question")
        samples = topic.get("short_question_samples", [])
        if len(samples) != len(topic["short_questions"]):
            raise ValueError(f"{slug}: warm-up questions need corresponding model answers")
        for sample in samples:
            localized(sample, f"{slug}/warm-up-model")
    return topics


def banks(content: Path, stage: str) -> tuple[list[dict], list[dict]]:
    stories = read(content / "library" / f"{stage}.json")["stories"]
    practice = read(content / "practice" / f"{stage}.json")["topics"]
    for directory in SUPPLEMENTS:
        path = content / directory / f"{stage}.json"
        if path.exists():
            addition = read(path)
            stories += addition.get("stories", [])
            practice += addition.get("topics", [])
    return stories, practice


def validate_pack(path: Path, stage: str, topics: dict[str, dict]) -> list[dict]:
    if not path.exists():
        return []
    data = read(path)
    if data.get("schema_version") != 1 or data.get("stage_id") != stage:
        raise ValueError(f"{path}: schema and stage must match the filename")
    if data.get("review_status") != "unreviewed":
        raise ValueError(f"{path}: human approval must not be invented")
    lessons = data.get("lessons", [])
    ids: set[str] = set()
    for lesson in lessons:
        identity = lesson.get("id", "")
        topic = lesson.get("topic_id")
        if topic not in topics:
            raise ValueError(f"{path}: unknown topic {topic}")
        if stage == "pre-a1" and not topics[topic].get("foundation_suitable"):
            raise ValueError(f"{identity}: pre-A1 must use a concrete foundation context")
        if not identity.startswith(f"{stage}-") or identity in ids:
            raise ValueError(f"{path}: unique stage-bound lesson IDs required")
        ids.add(identity)
        localized(lesson.get("title"), f"{identity}/title")
        lines = lesson.get("lines", [])
        if not 8 <= len(lines) <= 12:
            raise ValueError(f"{identity}: an original 8–12-sentence scene is required")
        for number, line in enumerate(lines, 1):
            localized(line, f"{identity}/line-{number}")
        for rule in lesson.get("grammar", []):
            localized(rule.get("title"), f"{identity}/grammar-title")
            localized(rule.get("explanation"), f"{identity}/grammar-explanation")
            examples = rule.get("examples", [])
            if not examples:
                raise ValueError(f"{identity}: grammar preparation requires an actual source example")
            for example in examples:
                localized(example, f"{identity}/grammar-example")
                if not any(all(normalized(example[lang]) in normalized(line[lang])
                               for lang in ("nl", "en")) for line in lines):
                    raise ValueError(f"{identity}: grammar example does not occur in this scene")
        for language in ("nl", "en"):
            values = [normalized(line[language]) for line in lines]
            if len(values) != len(set(values)):
                raise ValueError(f"{identity}: repeated sentences do not create a longer story")
        questions = lesson.get("questions", [])
        if len(questions) < 2:
            raise ValueError(f"{identity}: two grounded comprehension questions required")
        question_ids = set()
        for question in questions:
            qid = question.get("id")
            if not qid or qid in question_ids:
                raise ValueError(f"{identity}: comprehension question IDs must be distinct")
            question_ids.add(qid)
            localized(question.get("prompt"), f"{identity}/{qid}/prompt")
            localized(question.get("explanation"), f"{identity}/{qid}/explanation")
            options = question.get("options", [])
            answer = question.get("answer_index")
            if len(options) < 2 or type(answer) is not int or not 0 <= answer < len(options):
                raise ValueError(f"{identity}/{qid}: a valid keyed answer is required")
            for option in options:
                localized(option, f"{identity}/{qid}/option")
            if len({normalized(option["nl"]) for option in options}) != len(options):
                raise ValueError(f"{identity}/{qid}: answer choices must be distinct")
    return lessons


def make_index(content: Path, topics: list[dict]) -> dict:
    """Only explicit authored topic assignments enter the guided browser.

    Older banks stay available as vocabulary/grammar references. A word such as
    score, bank or kaart is not enough to relabel their stories as a new topic.
    Existing originals enter through an authored source_id or an explicit,
    manually checked source-map entry. Short originals do not become readings.
    """
    known = {topic["id"]: topic for topic in topics}
    source_document = read(content / "study" / "source-map.json")
    if set(source_document) != {"schema_version", "mappings"} or source_document["schema_version"] != 1:
        raise ValueError("unsupported explicit source mapping")
    manual = source_document["mappings"]
    if not isinstance(manual, list):
        raise TypeError("explicit source mappings must be a list")
    identities = set()
    for mapping in manual:
        if set(mapping) != {"stage_id", "topic_id", "source_id", "skills"}:
            raise ValueError("explicit source mapping has unsupported fields")
        if mapping["stage_id"] not in STAGES or mapping["topic_id"] not in known:
            raise ValueError("explicit source mapping has an unknown stage or canonical topic")
        if set(mapping["skills"]) != {"listening", "speaking", "writing"} or len(mapping["skills"]) != 3:
            raise ValueError("short source units belong to listening, speaking and writing only")
        identity = (mapping["stage_id"], mapping["source_id"])
        if identity in identities:
            raise ValueError("an original source unit must not be mapped twice")
        identities.add(identity)
    original_units = {
        (document["stage_id"], item["id"])
        for path in (content / "source-lessons").glob("*.json")
        for document in (read(path),)
        for item in document["topics"]
    }
    if identities != original_units:
        raise ValueError("every curated source unit requires one explicit guided topic mapping")
    stages = {}
    for stage in STAGES:
        skills: dict[str, dict[str, list[dict]]] = {skill: {} for skill in SKILLS}
        lessons = validate_pack(content / "study" / "packs" / f"{stage}.json", stage, known)
        stories, practice = banks(content, stage)
        originals = {item["id"] for item in [*stories, *practice]}
        for lesson in lessons:
            if lesson.get("source_id") and lesson["source_id"] not in originals:
                raise ValueError(f"{lesson['id']}: referenced original source does not exist in its stage")
            for skill in SKILLS:
                skills[skill].setdefault(lesson["topic_id"], []).append({"source": "pack", "id": lesson["id"]})
        stage_mappings = [mapping for mapping in manual if mapping["stage_id"] == stage]
        if stage_mappings:
            original_path = content / "source-lessons" / f"{stage}.json"
            source_topics = {item["id"] for item in read(original_path)["topics"]}
            pack_topics = {lesson["topic_id"] for lesson in lessons}
            for mapping in stage_mappings:
                if mapping["source_id"] not in source_topics:
                    raise ValueError(f"{stage}: explicit original practice source does not exist")
                if mapping["topic_id"] not in pack_topics:
                    raise ValueError(f"{stage}: source units may enrich only an existing authored topic")
                for skill in mapping["skills"]:
                    skills[skill][mapping["topic_id"]].append({"source": "practice", "id": mapping["source_id"]})
        stages[stage] = skills
    return {"schema_version": 1, "stages": stages}


def audit(content: Path, *, require_minimum: int = 50, source_index: dict | None = None) -> dict:
    topics = taxonomy(content)
    known = {topic["id"]: topic for topic in topics}
    seen: dict[str, str] = {}
    rows = []
    for stage in STAGES:
        lessons = validate_pack(content / "study" / "packs" / f"{stage}.json", stage, known)
        distinct_topics = {lesson["topic_id"] for lesson in lessons}
        if len(distinct_topics) < require_minimum:
            raise ValueError(f"{stage}: only {len(distinct_topics)} authored topics; {require_minimum} required")
        for lesson in lessons:
            text = normalized(" ".join(line["nl"] for line in lesson["lines"]))
            if text in seen:
                raise ValueError(f"{lesson['id']}: exact Dutch scene duplicates {seen[text]}")
            seen[text] = lesson["id"]
        rows.append({"stage": stage, "authored_topics": len(distinct_topics), "scenes": len(lessons),
                     "authored_grammar_lessons": sum(bool(lesson.get("grammar")) for lesson in lessons),
                     "review_status": "unreviewed"})
    index = source_index if source_index is not None else make_index(content, topics)
    for row in rows:
        row["available_topics"] = {skill: len(index["stages"][row["stage"]][skill]) for skill in SKILLS}
    return {"schema_version": 1, "claim": "Structural coverage only; CEFR, Dutch/English and acoustic review remain separate.",
            "canonical_topics": len(topics), "original_vocabulary_examples": sum(len(t["vocabulary"]) for t in topics),
            "stages": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=Path(__file__).resolve().parents[1] / "content")
    index_action = parser.add_mutually_exclusive_group()
    index_action.add_argument(
        "--write-index", action="store_true",
        help="Regenerate explicit source references after successful validation",
    )
    index_action.add_argument(
        "--check-index", action="store_true",
        help="Fail if checked-in references differ from the validated source mapping; never write files",
    )
    parser.add_argument("--allow-partial", action="store_true", help="Inspect authoring progress without asserting 50 topics")
    parser.add_argument("--json", type=Path, help="Optional private machine-readable audit output")
    args = parser.parse_args()
    index = make_index(args.content, taxonomy(args.content))
    result = audit(args.content, require_minimum=0 if args.allow_partial else 50, source_index=index)
    if args.check_index:
        path = args.content / "study" / "stage-index.json"
        stored = read(path) if path.exists() else None
        if stored != index:
            raise ValueError("guided source index is stale; regenerate with scripts/audit_guided_study.py --write-index")
        for stage in STAGES:
            for skill in SKILLS:
                actual = stored["stages"][stage][skill]
                if sum(bool(refs) for refs in actual.values()) < (0 if args.allow_partial else 50):
                    raise ValueError(f"{stage}/{skill}: checked-in sources do not meet the live topic minimum")
    if args.write_index:
        path = args.content / "study" / "stage-index.json"
        path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["claim"])
    for row in result["stages"]:
        counts = " ".join(f"{skill}={count}" for skill, count in row["available_topics"].items())
        print(f"{row['stage']:7} guided-scenes={row['scenes']:3} {counts}")


if __name__ == "__main__":
    main()
