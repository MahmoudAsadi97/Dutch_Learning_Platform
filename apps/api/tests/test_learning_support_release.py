"""Release boundaries for the new learner support workflows."""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from dlp.db.registry import Base

TABLES = {"topic_conversations", "practice_observations", "coach_plan_requests", "content_reviews"}


def test_support_migration_is_additive_and_models_have_privacy_cascades():
    root = Path(__file__).resolve().parents[1]
    output = io.StringIO()
    config = Config(str(root / "alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "0004:0005", sql=True)
    sql = output.getvalue()
    assert "DROP TABLE" not in sql
    for name in TABLES:
        assert f"CREATE TABLE {name}" in sql
        table = Base.metadata.tables[name]
        assert any(key.target_fullname == "learners.id" and key.ondelete == "CASCADE" for key in table.foreign_keys)
    assert sql.count("REFERENCES learners (id) ON DELETE CASCADE") == 4
    assert "UNIQUE (learner_id, source, request_id)" in sql
    assert "UNIQUE (cache_key)" in sql


def test_release_refuses_broken_conversations_before_database_connection(monkeypatch):
    from dlp import release
    order = []
    for name in ("curriculum", "validate_all_libraries", "validate_all_topics"):
        monkeypatch.setattr(release, name, lambda name=name: order.append(name))
    def invalid():
        order.append("conversations")
        raise ValueError("conversation points to a missing topic")
    monkeypatch.setattr(release, "validate_conversations", invalid)
    monkeypatch.setattr(release, "create_engine", lambda *args, **kwargs: order.append("database"))
    with pytest.raises(ValueError, match="missing topic"):
        release.migrate("postgresql+psycopg://dlp:dlp@localhost/dlp_test", "x" * 32)
    assert order == ["curriculum", "validate_all_libraries", "validate_all_topics", "conversations"]


def test_testing_cleanup_covers_new_history_and_queue_tables():
    from dlp.cli import LEARNER_DATA_TABLES
    from tests.conftest import TABLES_TO_CLEAR
    assert TABLES <= set(LEARNER_DATA_TABLES)
    assert TABLES <= set(TABLES_TO_CLEAR)


def test_fixture_does_not_claim_a_real_conversation_success():
    from dlp.domains.topic_conversations.schemas import TopicInterpretation
    from dlp.providers.base import ChatMessage
    from dlp.providers.fixtures import FixtureChatModel
    result = FixtureChatModel().complete_once([ChatMessage("user", "Ik kom om drie uur.")],
                                             schema=TopicInterpretation, prompt_version="topic-conversation-intent-v1")
    assert result.provider == "fixture"
    assert result.parsed.met is False
    assert result.parsed.quote == ""
