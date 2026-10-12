"""Rehearse a populated 0007 database upgrade inside an isolated, disposable test schema.

No downgrade, public-table cleanup, provider call or production connection is permitted here.
The existing CI PostgreSQL role owns its `_test` database, so it can create the temporary schema
without requiring a second database or a new infrastructure service.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from tests.conftest import TEST_DATABASE_URL


def _isolated_url(value: str, schema: str) -> URL:
    """Reject unsafe database/schema names before any database operation is possible."""
    url = make_url(value)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise ValueError("migration rehearsal requires a PostgreSQL database ending in _test")
    if not re.fullmatch(r"dlp_migration_rehearsal_[0-9a-f]{32}", schema):
        raise ValueError("migration rehearsal requires its own disposable schema name")
    # Exclude public entirely: an absent local alembic_version must never resolve to public's head.
    return url.update_query_dict({"options": f"-csearch_path={schema} -ctimezone=UTC -cstatement_timeout=30000"})


@pytest.mark.parametrize("value", [
    "postgresql+psycopg://owner@localhost/production",
    "postgresql+psycopg://owner@localhost/dlp",
    "sqlite:///dlp_test",
])
def test_populated_rehearsal_refuses_non_test_databases(value):
    with pytest.raises(ValueError, match="database ending in _test"):
        _isolated_url(value, "dlp_migration_rehearsal_" + "a" * 32)


@pytest.mark.parametrize("schema", ["public", "learner_data", "x;DROP SCHEMA public CASCADE", "dlp_migration_rehearsal_a"])
def test_populated_rehearsal_refuses_non_disposable_schemas(schema):
    with pytest.raises(ValueError, match="disposable schema"):
        _isolated_url("postgresql+psycopg://owner@localhost/dlp_test", schema)


def test_populated_rehearsal_has_no_public_search_path_fallback():
    schema = "dlp_migration_rehearsal_" + "a" * 32
    url = _isolated_url("postgresql+psycopg://owner@localhost/dlp_test", schema)
    assert url.query["options"].split()[0] == f"-csearch_path={schema}"
    assert "public" not in url.query["options"]


def _seed_0007(connection) -> dict[str, list[dict]]:
    """Use reflected 0007 columns, not the newer ORM, so this tests a real upgrade boundary."""
    metadata = MetaData()
    metadata.reflect(bind=connection)
    tables = metadata.tables
    learner, series, episode, word, counter, reservation = (uuid.uuid4() for _ in range(6))
    now = datetime(2026, 10, 1, 8, 30, tzinfo=UTC)
    day = date(2026, 10, 1)
    connection.execute(tables["learners"].insert(), {
        "id": learner, "subject": "migration-rehearsal:learner", "email": "migration@example.invalid",
        "display_name": "Rehearsal learner", "identity_provider": "fixture", "support_language": "fa",
        "target_language": "nl-BE", "notes": "Synthetic migration fixture", "created_at": now, "last_seen_at": now,
    })
    connection.execute(tables["story_series"].insert(), {
        "id": series, "learner_id": learner, "stage_id": "a1", "title": "Een gewone dag",
        "bible": {"cast": [{"name": "Lina"}]}, "memory": {"last_place": "Kortrijk"},
        "episode_count": 1, "created_at": now, "updated_at": now,
    })
    connection.execute(tables["story_episodes"].insert(), {
        "id": episode, "learner_id": learner, "series_id": series, "number": 1, "stage_id": "a1",
        "status": "ready", "error_code": "", "theme": "een afspraak", "theme_source": "learner",
        "topic_id": "appointment", "previous_choice": "", "title": "Een nieuwe afspraak",
        "paragraphs": [{"nl": "Lina maakt een afspraak.", "en": "Lina makes an appointment.",
                        "fa": "لینا یک قرار می‌گذارد."}],
        "glossary": [{"term": "de afspraak"}], "questions": [{"id": "q1"}], "choices": [{"id": "a"}],
        "recap": "Lina heeft een afspraak.", "mood": "calm", "word_count": 5, "checks": {"ok": True},
        "provider": "fixture", "model": "fixture", "prompt_version": "migration-fixture",
        "attempts": 1, "answers": {"q1": "a"}, "chosen_choice": "a", "rating": 2, "read_at": now,
        "created_at": now, "updated_at": now,
    })
    connection.execute(tables["vocab_items"].insert(), {
        "id": word, "learner_id": learner, "key": "de afspraak", "term": "de afspraak",
        "meaning_en": "appointment", "meaning_fa": "قرار", "example": "Ik heb morgen een afspraak.",
        "source_kind": "episode", "source_id": str(episode), "ease": 2.4, "interval_days": 7,
        "repetitions": 3, "lapses": 1, "last_grade": 2, "last_request_id": "migration-review",
        "due_at": now + timedelta(days=7), "reviewed_at": now, "created_at": now,
    })
    connection.execute(tables["usage_counters"].insert(), {
        "id": counter, "learner_id": learner, "scope": "daily", "period_key": day, "metric": "model_calls",
        "used": Decimal("8.000"), "reserved": Decimal("2.000"), "limit_value": Decimal("20.000"), "updated_at": now,
    })
    connection.execute(tables["usage_reservations"].insert(), {
        "id": reservation, "learner_id": learner, "metric": "model_calls", "request_id": "migration-reservation",
        "amount_reserved": Decimal("2.000"), "amount_used": Decimal("0.000"), "state": "reserved",
        "period_key": day, "created_at": now, "resolved_at": None,
    })
    connection.execute(tables["learning_days"].insert(), [
        {"id": uuid.uuid4(), "learner_id": learner, "day": day, "points": 22, "episodes_read": 1,
         "words_reviewed": 3, "questions_correct": 2, "read_aloud": 1, "goal_met": True, "updated_at": now},
        {"id": uuid.uuid4(), "learner_id": learner, "day": day + timedelta(days=1), "points": 0, "episodes_read": 0,
         "words_reviewed": 0, "questions_correct": 0, "read_aloud": 0, "goal_met": False, "updated_at": now},
    ])
    return {name: [dict(row) for row in connection.execute(select(tables[name]).order_by(tables[name].c.id)).mappings()]
            for name in ("learners", "story_series", "story_episodes", "vocab_items", "usage_counters",
                         "usage_reservations", "learning_days")}


def _assert_new_tables_usable(connection, learner_id: uuid.UUID) -> None:
    metadata = MetaData()
    metadata.reflect(bind=connection)
    tables = metadata.tables
    now = datetime(2026, 10, 2, 9, tzinfo=UTC)
    connection.execute(tables["learner_profiles"].insert(), {
        "id": uuid.uuid4(), "learner_id": learner_id, "created_at": now, "updated_at": now,
    })
    profile = connection.execute(select(tables["learner_profiles"])).mappings().one()
    assert profile["stage_id"] == "a1" and profile["daily_goal_points"] == 20 and profile["features"] == {}
    exercise_id, item_id = uuid.uuid4(), uuid.uuid4()
    connection.execute(tables["exercise_sessions"].insert(), {
        "id": exercise_id, "learner_id": learner_id, "request_id": "migration-session", "source": "topic",
        "stage_id": "a1", "skill": "reading", "seed": 1, "generator_version": "migration-test",
        "content_version": "migration-fixture", "created_at": now, "updated_at": now,
    })
    connection.execute(tables["exercise_items"].insert(), {
        "id": item_id, "session_id": exercise_id, "learner_id": learner_id, "position": 0,
        "kind": "reading_mcq", "skill": "reading", "ref": "migration-fixture",
        "prompt": {"nl": "Wanneer is de afspraak?"}, "key": {"answer": "a"},
    })
    item = connection.execute(select(tables["exercise_items"])).mappings().one()
    assert item["attempts"] == [] and item["first_outcome"] is None and item["hint_used"] is False
    connection.execute(tables["learner_mistakes"].insert(), {
        "id": uuid.uuid4(), "learner_id": learner_id, "source": "exercise", "source_id": str(item_id),
        "stage_id": "a1", "skill": "reading", "category": "meaning", "taxonomy_version": "v1", "created_at": now,
    })
    connection.execute(tables["word_suggestions"].insert(), {
        "id": uuid.uuid4(), "learner_id": learner_id, "key": "de tijd", "term": "de tijd", "reason": "revisit",
        "created_at": now, "updated_at": now,
    })
    assert connection.execute(select(tables["learner_mistakes"].c.assessed)).scalar_one() is True
    assert connection.execute(select(tables["word_suggestions"].c.status)).scalar_one() == "open"


@pytest.mark.db
def test_populated_0007_upgrades_to_head_without_losing_learning_or_usage(monkeypatch):
    schema = "dlp_migration_rehearsal_" + uuid.uuid4().hex
    isolated_url = _isolated_url(TEST_DATABASE_URL, schema)  # safety check precedes engine creation
    base_url = make_url(TEST_DATABASE_URL)
    admin = create_engine(base_url, poolclass=NullPool, hide_parameters=True,
                          connect_args={"connect_timeout": 5})
    scoped = create_engine(isolated_url, poolclass=NullPool, hide_parameters=True)
    created = False
    try:
        try:
            with admin.connect() as connection:
                connection.execute(text("SELECT 1"))
        except OperationalError:
            if os.environ.get("REQUIRE_TEST_DATABASE", "").lower() == "true":
                pytest.fail("required migration rehearsal test database is not reachable")
            pytest.skip("test PostgreSQL is not reachable for the populated migration rehearsal")
        with admin.begin() as connection:
            public_head = (list(connection.execute(text("SELECT version_num FROM public.alembic_version")).scalars())
                           if inspect(connection).has_table("alembic_version", schema="public") else None)
            connection.execute(text(f"CREATE SCHEMA {schema}"))
            created = True
        root = Path(__file__).resolve().parents[1]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        monkeypatch.setenv("ALEMBIC_DATABASE_URL", isolated_url.render_as_string(hide_password=False))
        command.upgrade(config, "0007")
        with scoped.begin() as connection:
            assert connection.execute(text("SELECT current_schema()")).scalar_one() == schema
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0007"
            assert not inspect(connection).has_table("learner_profiles", schema=schema)
            before = _seed_0007(connection)
        command.upgrade(config, "head")
        with scoped.begin() as connection:
            expected = frozenset(ScriptDirectory(str(root / "migrations")).get_heads())
            assert frozenset(connection.execute(text("SELECT version_num FROM alembic_version")).scalars()) == expected
            metadata = MetaData()
            metadata.reflect(bind=connection)
            for name, rows in before.items():
                table = metadata.tables[name]
                old_columns = [table.c[column] for column in rows[0]]
                after = [dict(row) for row in connection.execute(select(*old_columns).order_by(table.c.id)).mappings()]
                assert after == rows, f"0007 learning or usage data changed in {name}"
            events = list(connection.execute(select(metadata.tables["activity_events"])).mappings())
            assert len(events) == 1
            assert events[0]["kind"] == "legacy" and events[0]["points"] == 22 and events[0]["units"] == 0
            assert events[0]["day"] == date(2026, 10, 1) and events[0]["skill"] is None
            days = list(connection.execute(select(metadata.tables["learning_days"])).mappings())
            assert all(day["exercise_items"] == 0 and day["exercise_sessions"] == 0 for day in days)
            _assert_new_tables_usable(connection, before["learners"][0]["id"])
        # Public's migration marker is unchanged; the rehearsal never borrowed or advanced it.
        with admin.connect() as connection:
            after_public_head = (list(connection.execute(text("SELECT version_num FROM public.alembic_version")).scalars())
                                 if inspect(connection).has_table("alembic_version", schema="public") else None)
            assert after_public_head == public_head
    finally:
        scoped.dispose()
        if created:
            with admin.begin() as connection:
                connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin.dispose()
