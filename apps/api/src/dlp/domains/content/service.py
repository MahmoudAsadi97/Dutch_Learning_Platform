"""Loading, storing and reading mission documents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.config import CONTENT_DIR
from dlp.domains.content.models import Mission, MissionStep
from dlp.domains.content.schemas import MissionDocument, review_summary

MISSIONS_DIR = CONTENT_DIR / "missions"


class ContentError(Exception):
    pass


def canonical_json(document: MissionDocument) -> str:
    return json.dumps(document.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(document: MissionDocument) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def read_mission_file(path: Path) -> MissionDocument:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContentError(f"mission file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContentError(f"mission file is not valid JSON: {path}: {exc}") from exc
    document = MissionDocument.model_validate(raw)
    limit = document.content_pack.word_limit
    words = document.fixed_dutch_word_count()
    if words > limit:
        raise ContentError(f"mission {document.id}: fixed Dutch pack has {words} words, limit is {limit}")
    return document


def list_mission_files() -> list[Path]:
    if not MISSIONS_DIR.exists():
        return []
    return sorted(MISSIONS_DIR.glob("*/mission.json"))


def upsert_mission(session: Session, document: MissionDocument) -> Mission:
    """Store (or replace) the mission and its normalised steps. Idempotent for identical content."""
    digest = content_hash(document)
    mission = session.get(Mission, document.id)
    if mission is None:
        mission = Mission(id=document.id, version=document.version, cefr_target=document.cefr_target,
                          title_nl=document.title.nl, content_hash=digest, document={})
        session.add(mission)
    mission.version = document.version
    mission.cefr_target = document.cefr_target
    mission.title_nl = document.title.nl
    mission.title_fa = document.title.fa
    summary = review_summary(document)
    mission.review_status = "reviewed" if summary.unreviewed == 0 and summary.rejected == 0 else "unreviewed"
    mission.content_hash = digest
    mission.document = document.model_dump(mode="json")
    mission.fixed_word_count = document.fixed_dutch_word_count()
    mission.steps.clear()
    session.flush()
    for position, step in enumerate(document.steps):
        mission.steps.append(
            MissionStep(
                key=step.key,
                position=position,
                skill=step.skill,
                step_type=step.payload.type,
                variant=step.variant,
                payload=step.model_dump(mode="json"),
            )
        )
    session.flush()
    return mission


def load_all_missions(session: Session) -> list[Mission]:
    loaded: list[Mission] = []
    for path in list_mission_files():
        loaded.append(upsert_mission(session, read_mission_file(path)))
    return loaded


def get_mission(session: Session, mission_id: str) -> Mission | None:
    return session.get(Mission, mission_id)


def list_missions(session: Session) -> list[Mission]:
    return list(session.scalars(select(Mission).order_by(Mission.id)))


def mission_document(mission: Mission) -> MissionDocument:
    return MissionDocument.model_validate(mission.document)
