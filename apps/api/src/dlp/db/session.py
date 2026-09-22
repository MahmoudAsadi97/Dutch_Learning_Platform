from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from dlp.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        # Every connection reports timestamps in UTC, whatever the server's own time zone is, so the
        # ISO strings the API sends compare and sort the same way wherever they were loaded from.
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True, hide_parameters=True,
                                pool_size=5, max_overflow=5, pool_timeout=10,
                                connect_args={"options": "-c timezone=UTC -c statement_timeout=30000", "connect_timeout": 5})
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)
    return _engine


def reset_engine() -> None:
    """Dispose the engine so that a new configuration is picked up (tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def _factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    session = _factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, committed on success."""
    with session_scope() as session:
        yield session
