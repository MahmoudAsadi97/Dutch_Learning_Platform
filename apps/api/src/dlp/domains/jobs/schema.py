"""Stop an older worker claiming work after the release job has advanced the database."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.orm import Session


class SchemaVersionMismatch(RuntimeError):
    """The worker image and database do not have the same complete migration heads."""


@lru_cache(maxsize=4)
def _packaged_heads(api_dir: str) -> frozenset[str]:
    return frozenset(ScriptDirectory(str(Path(api_dir) / "migrations")).get_heads())


def require_current_schema(session: Session) -> None:
    """Check on every claim, not just startup: migrations can run while this image is still serving.

    Missing metadata or unreadable migration files fail closed through the worker's normal retry
    path. Exact heads also reject a database ahead of an old image, not only one behind it. This
    guard does not drain an already running handler; releases must still wait for active work.
    """
    api_dir = Path(os.environ.get("DLP_API_DIR", str(Path(__file__).resolve().parents[4]))).resolve()
    expected = _packaged_heads(str(api_dir))
    actual = frozenset(session.execute(text("SELECT version_num FROM alembic_version")).scalars())
    if not expected or actual != expected:
        raise SchemaVersionMismatch("worker paused: database migration heads do not match this image")
