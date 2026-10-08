"""Learner profile: one row per learner holding the level, the daily goal and the support language.

Revision ID: 0008
Revises: 0007
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False, server_default="a1"),
        sa.Column("daily_goal_points", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("support_mode", sa.String(10), nullable=True),
        sa.Column("gloss_mode", sa.String(8), nullable=False, server_default="auto"),
        sa.Column("stated_goal", sa.String(200), nullable=False, server_default=""),
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], name="fk_learner_profiles_learner_id_learners",
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_learner_profiles"),
        sa.UniqueConstraint("learner_id", name="uq_learner_profiles_learner_id"),
    )


def downgrade() -> None:
    op.drop_table("learner_profiles")
