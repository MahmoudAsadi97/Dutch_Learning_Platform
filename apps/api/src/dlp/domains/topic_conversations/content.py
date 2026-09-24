from functools import lru_cache
from pathlib import Path

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.curriculum.topics import topic_for, topics_for
from dlp.domains.topic_conversations.schemas import Blueprint, ConversationBank


@lru_cache(maxsize=2)
def _read(path: str, modified: int) -> ConversationBank:
    return ConversationBank.model_validate_json(Path(path).read_text(encoding="utf-8"))


def bank() -> ConversationBank:
    path = CONTENT_DIR / "conversations" / "pilot.json"
    return _read(str(path), path.stat().st_mtime_ns)


def blueprint_for(blueprint_id: str) -> Blueprint:
    item = next((item for item in bank().conversations if item.id == blueprint_id), None)
    if item is None:
        raise CurriculumError("conversation not found", 404)
    return item


def validate_conversations() -> ConversationBank:
    content = bank()
    for item in content.conversations:
        topic_for(topics_for(item.stage_id), item.topic_id)
    return content
