"""Stage-bound, authored vocabulary examples; no automatic inflection or level claims."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dlp.domains.curriculum.schemas import STAGE_IDS

# These are product sequencing limits, not an official grammar syllabus. A later
# stage can revisit an earlier structure. Beginner cards do not demand every tense.
STAGE_STRUCTURES = {
    "pre-a1": {"present", "noun_phrase", "adjective"},
    "a1": {"present", "future", "modal", "noun_phrase", "adjective"},
    "pre-a2": {"present", "future", "modal", "comparison", "noun_phrase", "adjective"},
}
ALL_STRUCTURES = {"present", "past", "future", "modal", "conditional", "comparison",
                  "register", "noun_phrase", "adjective", "other"}


class WordUsagePack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=1, le=1)
    stage_id: str
    review_status: str = Field(pattern="^unreviewed$")
    entries: list[dict] = Field(min_length=1)

    @model_validator(mode="after")
    def stage_and_entries(self):
        if self.stage_id not in STAGE_IDS:
            raise ValueError("word usage has an unknown stage")
        ids = [entry.get("word_id") for entry in self.entries]
        if any(not isinstance(key, str) or not key.startswith(f"{self.stage_id}-") for key in ids):
            raise ValueError("word usage IDs must belong to their stage")
        if len(set(ids)) != len(ids):
            raise ValueError("word usage cannot repeat a word")
        return self


def stamp(root: Path, stage_id: str) -> int:
    if stage_id not in STAGE_IDS:
        raise ValueError("word usage has an unknown stage")
    path = root / "vocabulary-transfer" / f"{stage_id}.json"
    if not path.exists():
        return 0
    stat = path.stat()
    return hash((stat.st_mtime_ns, stat.st_size))


@lru_cache(maxsize=24)
def _read(path: str, modified: int) -> WordUsagePack:
    pack = WordUsagePack.model_validate_json(Path(path).read_text(encoding="utf-8"))
    if pack.stage_id != Path(path).stem:
        raise ValueError("word usage stage does not match its file")
    return pack


def enrich(data: dict, root: Path) -> dict:
    """Overlay exact, existing word IDs without changing counts, meanings or evidence.

    Inflected forms and translations come from authored entries. Missing entries
    stay unchanged: a generic pattern is never advertised as a verified example.
    """
    # Imported here because library owns the public word schema and calls enrich.
    from dlp.domains.curriculum.library import LibraryWord

    result = deepcopy(data)
    stage_id = result["stage_id"]
    modified = stamp(root, stage_id)
    if not modified:
        return result
    pack = _read(str(root / "vocabulary-transfer" / f"{stage_id}.json"), modified)
    words = {item["id"]: item for item in result["vocabulary"]}
    allowed = STAGE_STRUCTURES.get(stage_id, ALL_STRUCTURES)
    fields = {"word_id", "term", "part_of_speech", "article", "plural", "forms", "contexts",
              "productive_core", "core_order"}
    for entry in pack.entries:
        if set(entry) - fields or "word_id" not in entry or "term" not in entry:
            raise ValueError("word usage contains unsupported fields")
        word = words.get(entry["word_id"])
        if word is None or word["term"] != entry["term"]:
            raise ValueError("word usage must match an existing word ID and term")
        updated = LibraryWord.model_validate({**word, **{k: v for k, v in entry.items() if k != "word_id"}})
        if len(updated.contexts) < 2:
            raise ValueError("transfer entries require at least two real situations")
        if any(context.structure not in allowed for context in updated.contexts):
            raise ValueError("word usage structure is outside this stage's sequencing limits")
        if any(not context.id.startswith(f"{updated.id}-") for context in updated.contexts):
            raise ValueError("word context IDs must belong to their word")
        word.update(updated.model_dump())
    return result
