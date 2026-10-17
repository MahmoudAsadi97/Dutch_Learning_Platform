"""Small original lesson additions; private scans and OCR are never loaded by the app."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question

DIRECTORIES = ("source-lessons", "learning-units", "reading-library")


def stamp(root: Path, stage_id: str) -> int:
    if stage_id not in STAGE_IDS:
        raise ValueError("supplement has an unknown learning stage")
    paths = [root / directory / f"{stage_id}.json" for directory in DIRECTORIES]
    versions = tuple((path.stat().st_mtime_ns, path.stat().st_size) if path.exists() else (0, 0) for path in paths)
    return hash(versions) if any(modified for modified, _ in versions) else 0


@lru_cache(maxsize=64)
def _read(path: str, version: tuple[int, int]) -> dict:
    # Import existing activity models only when loading: library/topics also use this
    # module, so module-level imports would create a circular dependency.
    from dlp.domains.curriculum.library import LibraryStory, LibraryWord
    from dlp.domains.curriculum.topics import PracticeTopic

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    fields = {"schema_version", "stage_id", "review_status", "vocabulary", "stories", "topics", "grammar_extensions"}
    if not isinstance(data, dict) or set(data) != fields:
        raise ValueError("supplement must contain only the supported lesson fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["review_status"] != "unreviewed":
        raise ValueError("unsupported supplement or unverified approval")
    stage_id = data["stage_id"]
    if stage_id not in STAGE_IDS or stage_id != Path(path).stem:
        raise ValueError("supplement stage does not match its file")
    for key in ("vocabulary", "stories", "topics", "grammar_extensions"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"supplement {key} must be a list")

    for key, model, prefix in (("vocabulary", LibraryWord, f"{stage_id}-"),
                               ("stories", LibraryStory, f"{stage_id}-"),
                               ("topics", PracticeTopic, f"{stage_id}-t")):
        items = [model.model_validate(item) for item in data[key]]
        if len({item.id for item in items}) != len(items) or any(not item.id.startswith(prefix) for item in items):
            raise ValueError(f"supplement {key} IDs must be unique and bound to their stage")
        for item in items:
            if key != "vocabulary" and any(not ref.startswith(f"{stage_id}-") for ref in item.vocabulary_ids):
                raise ValueError("supplement vocabulary references must belong to its stage")

    if Path(path).parent.name == "learning-units":
        topics = {item["id"]: item for item in data["topics"]}
        for story in data["stories"]:
            linked = topics.get(story.get("topic_id"))
            if not story.get("lines") or linked is None:
                raise ValueError("connected stories need authored lines and an existing topic link")
            if set(story["vocabulary_ids"]) != set(linked["vocabulary_ids"]):
                raise ValueError("connected story and topic must share their learning vocabulary")
            for language in ("nl", "en", "fa"):
                narrative = " ".join(p[language] for p in story["paragraphs"])
                reading = linked["reading"]["text"][language]
                if " ".join(narrative.split()) != " ".join(reading.split()):
                    raise ValueError("connected reading must preserve the story in each language")

    grammar_ids: set[str] = set()
    question_ids: set[str] = set()
    for extra in data["grammar_extensions"]:
        if not isinstance(extra, dict) or set(extra) != {"id", "examples", "practice"}:
            raise ValueError("supplement grammar extension has unsupported fields")
        if not isinstance(extra["id"], str) or not extra["id"].strip() or extra["id"] in grammar_ids:
            raise ValueError("supplement grammar targets must be unique")
        grammar_ids.add(extra["id"])
        for key in ("examples", "practice"):
            if not isinstance(extra[key], list):
                raise ValueError(f"supplement grammar {key} must be a list")
        for example in extra["examples"]:
            Localized.model_validate(example)
        for value in extra["practice"]:
            question = Question.model_validate(value)
            if not question.id.startswith(f"{stage_id}-") or question.id in question_ids:
                raise ValueError("supplement grammar questions must be unique and bound to their stage")
            question_ids.add(question.id)

    def check_copy(value):
        if isinstance(value, dict):
            if "nl" in value and any(not isinstance(value.get(lang), str) or not value[lang].strip()
                                      for lang in ("nl", "en", "fa")):
                raise ValueError("supplement learning copy needs all three nonblank languages")
            for child in value.values():
                check_copy(child)
        elif isinstance(value, list):
            for child in value:
                check_copy(child)

    check_copy(data)
    return data


def load(root: Path, stage_id: str) -> dict:
    result = {key: [] for key in ("vocabulary", "stories", "topics", "grammar_extensions")}
    if stage_id not in STAGE_IDS:
        raise ValueError("supplement has an unknown learning stage")
    for directory in DIRECTORIES:
        path = root / directory / f"{stage_id}.json"
        if path.exists():
            stat = path.stat()
            data = _read(str(path), (stat.st_mtime_ns, stat.st_size))
            for key in result:
                result[key].extend(deepcopy(data[key]))
    return result


def merge_bank(data: dict, root: Path, kind: str) -> dict:
    addition = load(root, data["stage_id"])
    keys = ("vocabulary", "stories") if kind == "library" else ("topics",)
    return {**data, **{key: data[key] + addition[key] for key in keys}}


def curriculum_stamp(root: Path) -> tuple[tuple[str, int], ...]:
    return tuple((p.stem, hash((p.stat().st_mtime_ns, p.stat().st_size))) for directory in DIRECTORIES
                 for p in sorted((root / directory).glob("*.json")))


def merge_curriculum(data: dict, root: Path) -> dict:
    data = deepcopy(data)
    known = {stage["id"] for stage in data["stages"]}
    if any(stage_id not in known for stage_id, _ in curriculum_stamp(root)):
        raise ValueError("supplement has an unknown learning stage")
    for stage in data["stages"]:
        grammar = {rule["id"]: rule for rule in stage["grammar"]}
        for extra in load(root, stage["id"])["grammar_extensions"]:
            if extra["id"] not in grammar:
                raise ValueError("supplement targets an unknown grammar rule")
            rule = grammar[extra["id"]]
            rule["examples"].extend(extra["examples"])
            rule["practice"].extend(extra["practice"])
    return data
