"""Read authored reading batches without importing runtime or schema modules.

The curriculum inventory and guided runtime share this small file boundary. It
does not classify stories, invent source identities or establish language review.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path


def reading_paths(root: Path, stage_id: str | None = None) -> tuple[Path, ...]:
    directory = root / "study" / "reading"
    paths = (directory / stage_id).glob("*.json") if stage_id else directory.glob("*/*.json")
    return tuple(sorted(paths))


def read_reading_batches(root: Path, stage_id: str | None = None) -> Iterator[tuple[str, Path, dict]]:
    """Yield the folder stage, exact path and raw document in deterministic order."""
    for path in reading_paths(root, stage_id):
        document = json.loads(path.read_text(encoding="utf-8"))
        stage = path.parent.name
        if not isinstance(document, dict) or document.get("stage_id") != stage:
            raise ValueError(f"{path}: reading batch stage does not match its directory")
        yield stage, path, document
