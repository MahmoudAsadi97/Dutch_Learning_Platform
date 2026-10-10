"""Exercise engine: sessions and their items, learner mistakes, word suggestions.

Revision ID: 0010
Revises: 0009
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def _learner(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], name=f"fk_{table}_learner_id_learners",
                                   ondelete="CASCADE")


def _json(name: str, default: str = "'{}'::jsonb") -> sa.Column:
    return sa.Column(name, postgresql.JSONB(), nullable=False, server_default=sa.text(default))


def upgrade() -> None:
    op.create_table(
        "exercise_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False, server_default=""),
        sa.Column("skill", sa.String(20), nullable=False, server_default=""),
        sa.Column("focus", sa.String(20), nullable=False, server_default=""),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("generator_version", sa.String(20), nullable=False),
        sa.Column("content_version", sa.String(64), nullable=False),
        _json("params"),
        sa.Column("status", sa.String(12), nullable=False, server_default="active"),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        _json("summary"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        _learner("exercise_sessions"),
        sa.PrimaryKeyConstraint("id", name="pk_exercise_sessions"),
        sa.UniqueConstraint("learner_id", "request_id", name="uq_exercise_sessions_learner_request"),
    )
    op.create_index("ix_exercise_sessions_learner_status", "exercise_sessions", ["learner_id", "status", "created_at"])
    op.create_table(
        "exercise_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False, server_default=""),
        sa.Column("ref", sa.String(120), nullable=False),
        sa.Column("word", sa.String(120), nullable=False, server_default=""),
        sa.Column("prompt", postgresql.JSONB(), nullable=False),
        sa.Column("key", postgresql.JSONB(), nullable=False),
        _json("attempts", "'[]'::jsonb"),
        sa.Column("first_outcome", sa.String(12), nullable=True),
        sa.Column("closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hint_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("points_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["exercise_sessions.id"],
                                name="fk_exercise_items_session_id_exercise_sessions", ondelete="CASCADE"),
        _learner("exercise_items"),
        sa.PrimaryKeyConstraint("id", name="pk_exercise_items"),
        sa.UniqueConstraint("session_id", "position", name="uq_exercise_items_session_position"),
    )
    op.create_index("ix_exercise_items_learner_ref", "exercise_items", ["learner_id", "ref"])
    op.create_index("ix_exercise_items_learner_word", "exercise_items", ["learner_id", "word"])
    op.create_table(
        "learner_mistakes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("source_id", sa.String(80), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False, server_default=""),
        sa.Column("kind", sa.String(24), nullable=False, server_default=""),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("taxonomy_version", sa.String(10), nullable=False),
        sa.Column("ref", sa.String(120), nullable=False, server_default=""),
        sa.Column("lemma", sa.String(120), nullable=False, server_default=""),
        sa.Column("given", sa.Text(), nullable=False, server_default=""),
        sa.Column("expected", sa.Text(), nullable=False, server_default=""),
        sa.Column("quote", sa.String(200), nullable=False, server_default=""),
        sa.Column("assessed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("request_id", sa.String(80), nullable=False, server_default=""),
        _json("detail"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _learner("learner_mistakes"),
        sa.PrimaryKeyConstraint("id", name="pk_learner_mistakes"),
        sa.UniqueConstraint("learner_id", "source", "source_id", name="uq_learner_mistakes_learner_source"),
    )
    op.create_index("ix_learner_mistakes_learner_created", "learner_mistakes", ["learner_id", "created_at"])
    op.create_index("ix_learner_mistakes_learner_category", "learner_mistakes", ["learner_id", "category"])
    op.create_index("ix_learner_mistakes_learner_ref", "learner_mistakes", ["learner_id", "ref"])
    op.create_table(
        "word_suggestions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("term", sa.String(120), nullable=False),
        sa.Column("meaning_en", sa.String(300), nullable=False, server_default=""),
        sa.Column("meaning_fa", sa.String(300), nullable=False, server_default=""),
        sa.Column("example", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_kind", sa.String(20), nullable=False, server_default="library"),
        sa.Column("source_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("reason", sa.String(20), nullable=False),
        sa.Column("miss_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(12), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _learner("word_suggestions"),
        sa.PrimaryKeyConstraint("id", name="pk_word_suggestions"),
        sa.UniqueConstraint("learner_id", "key", name="uq_word_suggestions_learner_key"),
    )


def downgrade() -> None:
    op.drop_table("word_suggestions")
    op.drop_index("ix_learner_mistakes_learner_ref", table_name="learner_mistakes")
    op.drop_index("ix_learner_mistakes_learner_category", table_name="learner_mistakes")
    op.drop_index("ix_learner_mistakes_learner_created", table_name="learner_mistakes")
    op.drop_table("learner_mistakes")
    op.drop_index("ix_exercise_items_learner_word", table_name="exercise_items")
    op.drop_index("ix_exercise_items_learner_ref", table_name="exercise_items")
    op.drop_table("exercise_items")
    op.drop_index("ix_exercise_sessions_learner_status", table_name="exercise_sessions")
    op.drop_table("exercise_sessions")
