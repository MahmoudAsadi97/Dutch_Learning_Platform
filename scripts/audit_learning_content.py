"""Audit legacy reference/practice banks, not the complete guided Reading catalogue.

Use validate_story_quality.py for canonical story targets across all sources and
audit_guided_study.py for the selectable learning route. No audit certifies CEFR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

STAGES = ("pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1", "pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2")


def audit(content: Path) -> dict:
    seen_terms: set[str] = set()
    seen_texts: dict[str, dict[str, str]] = {"reading": {}, "listening": {}}
    rows = []
    for stage in STAGES:
        library_path = content / "library" / f"{stage}.json"
        practice_path = content / "practice" / f"{stage}.json"
        library = json.loads(library_path.read_text(encoding="utf-8"))
        practice = json.loads(practice_path.read_text(encoding="utf-8"))
        supplement_path = content / "source-lessons" / f"{stage}.json"
        supplement_hash = None
        if supplement_path.exists():
            addition = json.loads(supplement_path.read_text(encoding="utf-8"))
            if (addition.get("schema_version") != 1 or addition.get("stage_id") != stage
                    or addition.get("review_status") != "unreviewed"):
                raise ValueError("Audit refuses an invalid or falsely approved source pack")
            library["vocabulary"] += addition["vocabulary"]
            library["stories"] += addition["stories"]
            practice["topics"] += addition["topics"]
            supplement_hash = hashlib.sha256(supplement_path.read_bytes()).hexdigest()
        unit_path = content / "learning-units" / f"{stage}.json"
        unit_hash = None
        if unit_path.exists():
            addition = json.loads(unit_path.read_text(encoding="utf-8"))
            if (addition.get("schema_version") != 1 or addition.get("stage_id") != stage
                    or addition.get("review_status") != "unreviewed"):
                raise ValueError("Audit refuses an invalid or falsely approved learning unit")
            library["vocabulary"] += addition["vocabulary"]
            library["stories"] += addition["stories"]
            practice["topics"] += addition["topics"]
            unit_hash = hashlib.sha256(unit_path.read_bytes()).hexdigest()
        reading_path = content / "reading-library" / f"{stage}.json"
        reading_hash = None
        if reading_path.exists():
            addition = json.loads(reading_path.read_text(encoding="utf-8"))
            if (addition.get("schema_version") != 1 or addition.get("stage_id") != stage
                    or addition.get("review_status") != "unreviewed"):
                raise ValueError("Audit refuses an invalid or falsely approved reading library")
            library["vocabulary"] += addition["vocabulary"]
            library["stories"] += addition["stories"]
            practice["topics"] += addition["topics"]
            reading_hash = hashlib.sha256(reading_path.read_bytes()).hexdigest()
        terms = {word["term"].strip().casefold() for word in library["vocabulary"]}
        repeated = {"reading": [], "listening": []}
        for topic in practice["topics"]:
            for skill, duplicates in repeated.items():
                text = " ".join(topic[skill]["text"]["nl"].split())
                if text in seen_texts[skill] and seen_texts[skill][text] != stage:
                    duplicates.append({"topic_id": topic["id"], "review_of": seen_texts[skill][text]})
                seen_texts[skill].setdefault(text, stage)
        rows.append({
            "stage": stage, "vocabulary": len(library["vocabulary"]), "distinct_terms": len(terms),
            "new_terms_relative_to_earlier_banks": len(terms - seen_terms),
            "stories": len(library["stories"]), "topics_per_skill": len(practice["topics"]),
            "review_status": {"library": library.get("review_status", "unknown"),
                              "practice": practice.get("review_status", "unknown")},
            "reused_texts": repeated,
            "content_sha256": {"library": hashlib.sha256(library_path.read_bytes()).hexdigest(),
                               "practice": hashlib.sha256(practice_path.read_bytes()).hexdigest(),
                               "supplement": supplement_hash, "learning_units": unit_hash,
                               "reading_library": reading_hash},
        })
        seen_terms.update(terms)
    return {"schema_version": 2,
            "scope": "Legacy reference/practice banks and their supplements; guided Reading is audited separately.",
            "claim": "Legacy bank coverage and duplication only; no canonical story target, level or language validation.",
            "stages": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=Path(__file__).resolve().parents[1] / "content")
    parser.add_argument("--json", type=Path, help="Optional audit output path; no learner records are read.")
    args = parser.parse_args()
    result = audit(args.content)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["claim"])
    for row in result["stages"]:
        counts = {skill: len(items) for skill, items in row["reused_texts"].items()}
        print(f"{row['stage']:7} words={row['vocabulary']} new={row['new_terms_relative_to_earlier_banks']} "
              f"legacy-bank-stories={row['stories']} topics/skill={row['topics_per_skill']} reused={counts}")


if __name__ == "__main__":
    main()
