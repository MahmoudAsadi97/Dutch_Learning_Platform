"""Read published story counts and legacy eligibility without repeating the editorial audit.

The release check verifies this compact artifact against the full audit. Runtime
accepts it only while the source fingerprint matches; edited or missing content
falls back to the shared audit until the catalogue is regenerated.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from dlp.domains.curriculum.schemas import STAGE_IDS

MANIFEST = "study/reading-eligibility.json"
DIRECTORIES = ("library", "source-lessons", "learning-units", "reading-library", "study/packs", "vocabulary-transfer")
COUNTS = ("authored_stories", "eligible_authored_stories", "legacy_stories", "legacy_library_stories_total",
          "legacy_library_authored_stories", "legacy_library_eligible_stories")


def source_stamp(root: Path) -> tuple[tuple[str, int, int], ...]:
    paths = [root / "alignment/story-provenance.json", root / "study/reading-map.json"]
    paths.extend(root / directory / f"{stage}.json" for directory in DIRECTORIES for stage in STAGE_IDS)
    paths.extend((root / "study/reading").glob("*/*.json"))
    return tuple((str(path.relative_to(root)), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in sorted(paths) if path.exists())


@lru_cache(maxsize=4)
def _fingerprint(root: str, version: tuple) -> str:
    digest = hashlib.sha256()
    for relative, _, _ in version:
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update((Path(root) / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build(root: Path, audited: dict) -> dict:
    return {"schema_version": 1, "source_sha256": _fingerprint(str(root), source_stamp(root)),
            "stages": {row["stage"]: {"eligible_ids": sorted(row["legacy_library_eligible_story_ids"]),
                                      "counts": {key: row[key] for key in COUNTS}} for row in audited["stages"]}}


@lru_cache(maxsize=4)
def _load(root: str, source_version: tuple, artifact_version: tuple) -> dict | None:
    try:
        document = json.loads((Path(root) / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (not isinstance(document, dict) or set(document) != {"schema_version", "source_sha256", "stages"}
            or type(document["schema_version"]) is not int or document["schema_version"] != 1
            or not isinstance(document["stages"], dict)
            or set(document["stages"]) != set(STAGE_IDS)
            or document["source_sha256"] != _fingerprint(root, source_version)):
        return None
    for stage, row in document["stages"].items():
        if (not isinstance(row, dict) or set(row) != {"eligible_ids", "counts"}
                or not isinstance(row["counts"], dict) or set(row["counts"]) != set(COUNTS)
                or any(type(value) is not int or value < 0 for value in row["counts"].values())):
            return None
        identities = row["eligible_ids"]
        if (not isinstance(identities, list)
                or any(not isinstance(identity, str) or not identity.startswith(stage + "-")
                       or not re.fullmatch(r"[a-z0-9-]+", identity) for identity in identities)
                or len(identities) != len(set(identities))
                or len(identities) != row["counts"]["legacy_library_eligible_stories"]):
            return None
    return document


def _document(root: Path) -> dict | None:
    path = root / MANIFEST
    if not path.exists():
        return None
    stat = path.stat()
    return _load(str(root), source_stamp(root), (stat.st_mtime_ns, stat.st_size))


def eligible_story_ids(root: Path, stage: str) -> frozenset[str] | None:
    document = _document(root)
    return frozenset(document["stages"].get(stage, {}).get("eligible_ids", [])) if document is not None else None


def stage_counts(root: Path) -> dict[str, dict] | None:
    document = _document(root)
    return {stage: dict(row["counts"]) for stage, row in document["stages"].items()} if document is not None else None
