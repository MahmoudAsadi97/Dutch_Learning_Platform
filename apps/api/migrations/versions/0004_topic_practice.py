"""Learner-owned four-skill topic progress and latest evidence.

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_practice",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("latest_passed", sa.Boolean(), nullable=False),
        sa.Column("content_version", sa.String(64), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_id", "stage_id", "topic_id", "skill"),
    )


def downgrade() -> None:
    op.drop_table("topic_practice")
