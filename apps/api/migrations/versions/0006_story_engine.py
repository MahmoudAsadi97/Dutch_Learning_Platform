"""Story serial, generated episodes, the personal word bank and daily activity.

Revision ID: 0006
Revises: 0005
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def _learner():
    return sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE")


def upgrade() -> None:
    op.create_table(
        "story_series",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("bible", postgresql.JSONB(), nullable=False),
        sa.Column("memory", postgresql.JSONB(), nullable=False),
        sa.Column("episode_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id"),
    )
    op.create_table(
        "story_episodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=False),
        sa.Column("theme", sa.String(160), nullable=False),
        sa.Column("theme_source", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("previous_choice", sa.String(160), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("paragraphs", postgresql.JSONB(), nullable=False),
        sa.Column("glossary", postgresql.JSONB(), nullable=False),
        sa.Column("questions", postgresql.JSONB(), nullable=False),
        sa.Column("choices", postgresql.JSONB(), nullable=False),
        sa.Column("recap", sa.Text(), nullable=False),
        sa.Column("mood", sa.String(30), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("checks", postgresql.JSONB(), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("chosen_choice", sa.String(8), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _learner(),
        sa.ForeignKeyConstraint(["series_id"], ["story_series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("series_id", "number"),
    )
    op.create_index("ix_story_episodes_learner_status", "story_episodes", ["learner_id", "status", "created_at"])
    op.create_table(
        "vocab_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("term", sa.String(120), nullable=False),
        sa.Column("meaning_en", sa.String(300), nullable=False),
        sa.Column("meaning_fa", sa.String(300), nullable=False),
        sa.Column("example", sa.Text(), nullable=False),
        sa.Column("source_kind", sa.String(20), nullable=False),
        sa.Column("source_id", sa.String(80), nullable=False),
        sa.Column("ease", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.Column("last_grade", sa.Integer(), nullable=True),
        sa.Column("last_request_id", sa.String(80), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id", "key"),
    )
    op.create_index("ix_vocab_items_learner_due", "vocab_items", ["learner_id", "due_at"])
    op.create_table(
        "learning_days",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("episodes_read", sa.Integer(), nullable=False),
        sa.Column("words_reviewed", sa.Integer(), nullable=False),
        sa.Column("questions_correct", sa.Integer(), nullable=False),
        sa.Column("read_aloud", sa.Integer(), nullable=False),
        sa.Column("goal_met", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id", "day"),
    )


def downgrade() -> None:
    op.drop_table("learning_days")
    op.drop_index("ix_vocab_items_learner_due", table_name="vocab_items")
    op.drop_table("vocab_items")
    op.drop_index("ix_story_episodes_learner_status", table_name="story_episodes")
    op.drop_table("story_episodes")
    op.drop_table("story_series")
