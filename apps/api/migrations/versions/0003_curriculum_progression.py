"""Twelve-stage learning path practice and final checks.

Revision ID: 0003
Revises: 0002
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "curriculum_practice",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_id", "stage_id", "skill"),
    )
    op.create_table(
        "curriculum_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("content_version", sa.String(64), nullable=False),
        sa.Column("test_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("submission", postgresql.JSONB(), nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=False),
        sa.Column("speaking_asset_id", sa.UUID(), nullable=True),
        sa.Column("admin_preview", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["speaking_asset_id"], ["audio_assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_id", "request_id"),
        sa.UniqueConstraint("speaking_asset_id"),
    )
    op.create_index("ix_curriculum_attempts_learner_stage", "curriculum_attempts", ["learner_id", "stage_id"])


def downgrade() -> None:
    op.drop_index("ix_curriculum_attempts_learner_stage", table_name="curriculum_attempts")
    op.drop_table("curriculum_attempts")
    op.drop_table("curriculum_practice")
