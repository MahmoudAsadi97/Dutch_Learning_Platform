"""Validate guided topic packs and regenerate their source index on request.

This checks coverage, references, translations and exact repetition structurally.
It cannot certify CEFR difficulty, natural language, pronunciation or translation
accuracy. Dutch/English review remains a separate, recorded editorial step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

from dlp.domains.study.reading_sources import read_reading_batches

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


def validate_pack(path: Path, stage: str, topics: dict[str, dict], *,
                  data: dict | None = None, reading_only: bool = False) -> list[dict]:
    if data is None and not path.exists():
        return []
    data = read(path) if data is None else data
    if data.get("schema_version") != 1 or data.get("stage_id") != stage:
        raise ValueError(f"{path}: schema and stage must match the filename")
    if data.get("review_status") != "unreviewed":
        raise ValueError(f"{path}: human approval must not be invented")
    if reading_only and data.get("language_variety") != "nl-BE":
        raise ValueError(f"{path}: original readings require Belgian Standard Dutch")
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
        if reading_only:
            if not identity.startswith(f"{stage}-read-") or len(identity) > 100:
                raise ValueError(f"{path}: original readings require exact stage-bound reading IDs")
            if not isinstance(lesson.get("plot_key"), str) or len(lesson["plot_key"].strip()) < 20:
                raise ValueError(f"{identity}: an original concrete plot synopsis is required")
            if lesson.get("source_id") is not None or any(lesson.get(skill) is not None
                                                         for skill in ("speaking", "writing", "listening")):
                raise ValueError(f"{identity}: reading batches must remain original and reading-only")
        ids.add(identity)
        localized(lesson.get("title"), f"{identity}/title")
        lines = lesson.get("lines", [])
        if not 8 <= len(lines) <= 12:
            raise ValueError(f"{identity}: an original 8–12-sentence scene is required")
        for number, line in enumerate(lines, 1):
            localized(line, f"{identity}/line-{number}")
        if reading_only:
            exact_lines = {(normalized(line["nl"]), normalized(line["en"])) for line in lines}
            words = lesson.get("words", [])
            if not 3 <= len(words) <= 20 or len({normalized(word.get("term", "")) for word in words}) != len(words):
                raise ValueError(f"{identity}: at least three distinct prepared words are required")
            for word in words:
                localized(word.get("meaning"), f"{identity}/{word.get('term')}/meaning")
                localized(word.get("example"), f"{identity}/{word.get('term')}/example")
                if word.get("minimum_stage") != stage or not word.get("part_of_speech"):
                    raise ValueError(f"{identity}: reading words need their authored stage and word class")
                if (normalized(word["example"]["nl"]), normalized(word["example"]["en"])) not in exact_lines:
                    raise ValueError(f"{identity}: word preparation must use an exact bilingual story line")
            if not lesson.get("grammar"):
                raise ValueError(f"{identity}: an original reading needs source-grounded grammar preparation")
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
                if reading_only and (normalized(example["nl"]), normalized(example["en"])) not in exact_lines:
                    raise ValueError(f"{identity}: grammar preparation must preserve an exact bilingual story line")
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


def reading_lessons(content: Path, topics: dict[str, dict]) -> dict[str, list[dict]]:
    """Keep original batch identities and explicit topic assignments unchanged."""
    stages: dict[str, list[dict]] = {stage: [] for stage in STAGES}
    identities: set[str] = set()
    plots: set[str] = set()
    for stage, path, document in read_reading_batches(content):
        if stage not in STAGES:
            raise ValueError(f"{path}: reading batch has an unknown stage")
        lessons = validate_pack(path, stage, topics, data=document, reading_only=True)
        for lesson in lessons:
            plot = normalized(lesson["plot_key"])
            if lesson["id"] in identities or plot in plots:
                raise ValueError(f"{lesson['id']}: reading batches repeat an identity or plot")
            identities.add(lesson["id"])
            plots.add(plot)
        stages[stage].extend(lessons)
    return stages


def reading_mappings(content: Path, topics: dict[str, dict]) -> list[dict]:
    path = content / "study" / "reading-map.json"
    if not path.exists():
        return []
    document = read(path)
    if set(document) != {"schema_version", "mappings"} or document["schema_version"] != 1:
        raise ValueError("unsupported explicit reading mapping")
    mappings = document["mappings"]
    if not isinstance(mappings, list):
        raise TypeError("reading mappings must be an authored list")
    identities: set[tuple[str, str]] = set()
    for mapping in mappings:
        if set(mapping) != {"stage_id", "topic_id", "story_id"}:
            raise ValueError("reading mapping has unsupported fields")
        if mapping["stage_id"] not in STAGES or mapping["topic_id"] not in topics:
            raise ValueError("reading mapping requires a known stage and canonical topic")
        identity = (mapping["stage_id"], mapping["story_id"])
        if identity in identities:
            raise ValueError("an original reading may belong to only one topic")
        identities.add(identity)
    return mappings


def make_index(content: Path, topics: list[dict]) -> dict:
    """Only explicit authored topic assignments enter the guided browser.

    Older banks stay available as vocabulary/grammar references. A word such as
    score, bank or kaart is not enough to relabel their stories as a new topic.
    Existing originals enter through an authored source_id or an explicit,
    manually checked source-map entry. Short originals do not become readings.
    """
    known = {topic["id"]: topic for topic in topics}
    readings = reading_lessons(content, known)
    mapped_readings = reading_mappings(content, known)
    # Reuse the catalogue's structural exclusions. A short template does not
    # become an authored reading merely by receiving a canonical topic label.
    from dlp.domains.curriculum.story_inventory import audit as story_audit

    audited = story_audit(content)
    eligible = {row["stage"]: set(row["legacy_library_eligible_story_ids"]) for row in audited["stages"]}
    published_readings = {(record["stage_id"], record["source_kind"], record["source_id"])
                          for record in audited["canonical_stories"] if record["eligible"]}
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
                if skill == "reading" and (stage, "guided", lesson["id"]) not in published_readings:
                    continue
                skills[skill].setdefault(lesson["topic_id"], []).append({"source": "pack", "id": lesson["id"]})
        for lesson in readings[stage]:
            if (stage, "reading", lesson["id"]) in published_readings:
                skills["reading"].setdefault(lesson["topic_id"], []).append({"source": "reading", "id": lesson["id"]})
        adapted = {lesson["source_id"] for lesson in lessons if lesson.get("source_id")}
        original_stories = {story["id"]: story for story in stories}
        assignments = {mapping["story_id"]: mapping["topic_id"]
                       for mapping in mapped_readings if mapping["stage_id"] == stage}
        for story_id, topic_id in assignments.items():
            if story_id not in original_stories or story_id not in eligible[stage]:
                raise ValueError(f"{stage}: explicit reading mapping must resolve to an eligible original story")
            declared = original_stories[story_id].get("topic_id")
            if declared in known and declared != topic_id:
                raise ValueError(f"{story_id}: explicit reading mapping contradicts its authored topic")
        for story in stories:
            # Old topic IDs used by another lesson engine are not canonical
            # labels. Only an actual canonical assignment or reviewed manifest
            # entry permits an original story into this topic browser.
            topic_id = assignments.get(story["id"], story.get("topic_id"))
            if (topic_id not in known or story["id"] not in eligible[stage] or story["id"] in adapted
                    or (stage, "library", story["id"]) not in published_readings):
                continue
            if stage == "pre-a1" and not known[topic_id].get("foundation_suitable"):
                raise ValueError(f"{story['id']}: pre-A1 reading requires a concrete foundation topic")
            skills["reading"].setdefault(topic_id, []).append({"source": "story", "id": story["id"]})
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


def validate_reading_reachability(index: dict, records: list[dict]) -> dict[str, int]:
    """Every counted story must have one reachable, stage-correct Reading entry."""
    source_names = {"guided": "pack", "library": "story", "reading": "reading"}
    expected = {
        (record["stage_id"], source_names[record["source_kind"]], record["source_id"])
        for record in records if record["eligible"]
    }
    actual = Counter(
        (stage, reference["source"], reference["id"])
        for stage, skills in index["stages"].items()
        for references in skills.get("reading", {}).values()
        for reference in references
    )
    missing = expected - actual.keys()
    unexpected = actual.keys() - expected
    repeated = {identity for identity, count in actual.items() if count != 1}
    if missing or unexpected or repeated:
        raise ValueError(
            "Reading inventory must match the selectable catalogue exactly: "
            f"{len(missing)} missing, {len(unexpected)} uncounted, {len(repeated)} repeated entries"
        )
    return dict(Counter(stage for stage, _, _ in expected))


def audit(content: Path, *, require_minimum: int = 50, source_index: dict | None = None) -> dict:
    topics = taxonomy(content)
    known = {topic["id"]: topic for topic in topics}
    readings = reading_lessons(content, known)
    seen: dict[str, str] = {}
    rows = []
    for stage in STAGES:
        lessons = validate_pack(content / "study" / "packs" / f"{stage}.json", stage, known)
        distinct_topics = {lesson["topic_id"] for lesson in lessons}
        if len(distinct_topics) < require_minimum:
            raise ValueError(f"{stage}: only {len(distinct_topics)} authored topics; {require_minimum} required")
        for lesson in [*lessons, *readings[stage]]:
            text = normalized(" ".join(line["nl"] for line in lesson["lines"]))
            if text in seen:
                raise ValueError(f"{lesson['id']}: exact Dutch scene duplicates {seen[text]}")
            seen[text] = lesson["id"]
        rows.append({"stage": stage, "authored_topics": len(distinct_topics), "scenes": len(lessons),
                     "reading_scenes": len(readings[stage]),
                     "authored_grammar_lessons": sum(bool(lesson.get("grammar")) for lesson in lessons),
                     "review_status": "unreviewed"})
    index = source_index if source_index is not None else make_index(content, topics)
    from dlp.domains.curriculum.story_inventory import canonical_story_records

    reachable = validate_reading_reachability(index, canonical_story_records(content))
    for row in rows:
        row["selectable_readings"] = reachable.get(row["stage"], 0)
        row["available_topics"] = {skill: len(index["stages"][row["stage"]][skill]) for skill in SKILLS}
        for skill, count in row["available_topics"].items():
            if count < require_minimum:
                raise ValueError(f"{row['stage']}/{skill}: only {count} selectable topics; {require_minimum} required")
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
    from dlp.domains.curriculum import reading_manifest, story_inventory

    eligibility = reading_manifest.build(args.content, story_inventory.audit(args.content))
    if args.check_index:
        path = args.content / "study" / "stage-index.json"
        stored = read(path) if path.exists() else None
        if stored != index:
            raise ValueError("guided source index is stale; regenerate with scripts/audit_guided_study.py --write-index")
        manifest_path = args.content / reading_manifest.MANIFEST
        if not manifest_path.exists() or read(manifest_path) != eligibility:
            raise ValueError("reading eligibility is stale; regenerate with scripts/audit_guided_study.py --write-index")
        for stage in STAGES:
            for skill in SKILLS:
                actual = stored["stages"][stage][skill]
                if sum(bool(refs) for refs in actual.values()) < (0 if args.allow_partial else 50):
                    raise ValueError(f"{stage}/{skill}: checked-in sources do not meet the live topic minimum")
    if args.write_index:
        path = args.content / "study" / "stage-index.json"
        path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.content / reading_manifest.MANIFEST).write_text(
            json.dumps(eligibility, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["claim"])
    for row in result["stages"]:
        counts = " ".join(f"{skill}={count}" for skill, count in row["available_topics"].items())
        print(f"{row['stage']:7} guided-scenes={row['scenes']:3} original-readings={row['reading_scenes']:3} {counts}")


if __name__ == "__main__":
    main()
