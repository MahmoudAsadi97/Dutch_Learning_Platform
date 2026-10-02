"""Video lessons: presenter videos at the learner's level about a chosen topic.

Revision ID: 0007
Revises: 0006
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_lessons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("topic", sa.String(160), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("scenes", postgresql.JSONB(), nullable=False),
        sa.Column("glossary", postgresql.JSONB(), nullable=False),
        sa.Column("questions", postgresql.JSONB(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("checks", postgresql.JSONB(), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("renderer", sa.String(60), nullable=False),
        sa.Column("render_job_id", sa.String(120), nullable=False),
        sa.Column("render_polls", sa.Integer(), nullable=False),
        sa.Column("voice", sa.String(80), nullable=False),
        sa.Column("presenter", sa.String(80), nullable=False),
        sa.Column("media_key", sa.String(300), nullable=False),
        sa.Column("media_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("cues", postgresql.JSONB(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_lessons_learner_status", "video_lessons", ["learner_id", "status", "created_at"])
    op.add_column("learning_days", sa.Column("videos_watched", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("learning_days", "videos_watched")
    op.drop_index("ix_video_lessons_learner_status", table_name="video_lessons")
    op.drop_table("video_lessons")
