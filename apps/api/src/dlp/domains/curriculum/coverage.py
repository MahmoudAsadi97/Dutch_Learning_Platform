"""Content-backed catalogue counts; inventory targets never imply language approval.

The cached version includes every source used by the effective banks and the story
provenance audit. Nothing is counted from a hard-coded marketing total.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import grammar, story_inventory, supplements, word_usage
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS, Curriculum, Stage

if TYPE_CHECKING:
    from dlp.domains.curriculum.library import StageLibrary
    from dlp.domains.curriculum.topics import TopicBank

TARGETS = {"words": 500, "productive_core": 150, "authored_stories": 200,
           "grammar_questions": 100, "skill_topics": 100}
CLAIM = "Content inventory only; counts do not establish language accuracy, CEFR calibration or learner mastery."
DIRECTORIES = (*story_inventory.PACKS, "practice", "vocabulary-transfer", "grammar-bank")


def content_stamp(root: Path) -> tuple[tuple[str, int, int], ...]:
    paths = [root / "curriculum/path.json", root / "alignment/story-provenance.json"]
    paths.extend(root / directory / f"{stage}.json" for directory in DIRECTORIES for stage in STAGE_IDS)
    return tuple((str(path.relative_to(root)), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in paths if path.exists())


def stage_coverage(stage: Stage, bank: StageLibrary, topic_bank: TopicBank, audited: dict) -> dict:
    """Count validated, effective content, keeping legacy stories out of the target."""
    counts = {
        "words": len(bank.vocabulary),
        "productive_core": sum(word.productive_core for word in bank.vocabulary),
        "productive_contexts": sum(len(word.contexts) for word in bank.vocabulary if word.productive_core),
        "authored_stories": audited["authored_stories"],
        "eligible_authored_stories": audited["eligible_authored_stories"],
        "legacy_stories": audited["legacy_stories"],
        "total_stories": len(bank.stories),
        "grammar_questions": sum(len(rule.practice) for rule in stage.grammar),
        "grammar_topics": len(stage.grammar),
        "skill_topics": {skill: len(topic_bank.topics) for skill in SKILLS},
    }
    shortfalls = {key: max(0, TARGETS[key] - counts[key])
                  for key in ("words", "productive_core", "grammar_questions")}
    shortfalls["authored_stories"] = max(0, TARGETS["authored_stories"] - counts["eligible_authored_stories"])
    shortfalls["skill_topics"] = {skill: max(0, TARGETS["skill_topics"] - total)
                                 for skill, total in counts["skill_topics"].items()}
    return {**counts, "targets": dict(TARGETS), "shortfalls": shortfalls, "review_status": bank.review_status}


@lru_cache(maxsize=4)
def _story_audit(root_path: str, version: tuple) -> dict:
    return story_inventory.audit(Path(root_path))


@lru_cache(maxsize=4)
def _read(root_path: str, version: tuple) -> dict[str, dict]:
    # Lazy imports preserve the existing service/library dependency boundary.
    from dlp.domains.curriculum import library, topics

    root = Path(root_path)
    path = root / "curriculum/path.json"
    curriculum_data = json.loads(path.read_text(encoding="utf-8"))
    document = Curriculum.model_validate(grammar.merge(supplements.merge_curriculum(curriculum_data, root), root))
    audit = _story_audit(root_path, version)
    audited_stages = {row["stage"]: row for row in audit["stages"]}
    result = {}
    for stage in document.stages:
        library_path = root / "library" / f"{stage.id}.json"
        bank = library._read(str(library_path), library_path.stat().st_mtime_ns, supplements.stamp(root, stage.id),
                             word_usage.stamp(root, stage.id))
        topic_path = root / "practice" / f"{stage.id}.json"
        topic_bank = topics._read(str(topic_path), topic_path.stat().st_mtime_ns, supplements.stamp(root, stage.id))
        if bank.stage_id != stage.id or topic_bank.stage_id != stage.id:
            raise ValueError("content inventory stage does not match its requested file")
        known_words = {word.id for word in bank.vocabulary}
        if any(not set(topic.vocabulary_ids).issubset(known_words) for topic in topic_bank.topics):
            raise ValueError("content inventory topic refers to vocabulary outside its stage")
        result[stage.id] = stage_coverage(stage, bank, topic_bank, audited_stages[stage.id])
    return result


def all_coverage() -> dict[str, dict]:
    return _read(str(CONTENT_DIR), content_stamp(CONTENT_DIR))


def eligible_story_ids(stage_id: str) -> frozenset[str]:
    """Use exactly the CLI audit exclusions, cached once for each content version."""
    audit = _story_audit(str(CONTENT_DIR), content_stamp(CONTENT_DIR))
    row = next((item for item in audit["stages"] if item["stage"] == stage_id), None)
    return frozenset(row["eligible_authored_story_ids"]) if row else frozenset()


def report() -> dict:
    values = all_coverage()
    return {"claim": CLAIM, "targets": dict(TARGETS),
            "stages": [{"stage_id": stage_id, **values[stage_id]} for stage_id in STAGE_IDS]}
