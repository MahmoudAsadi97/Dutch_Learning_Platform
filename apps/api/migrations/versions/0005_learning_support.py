"""Bounded topic conversations, observation history, plans and editing suggestions.

Revision ID: 0005
Revises: 0004
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _learner():
    return sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE")


def upgrade() -> None:
    op.create_table(
        "topic_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("blueprint_id", sa.String(80), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("topic_content_version", sa.String(64), nullable=False),
        sa.Column("mode", sa.String(12), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("blueprint", postgresql.JSONB(), nullable=False),
        sa.Column("history", postgresql.JSONB(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("assisted_steps", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id", "request_id"),
    )
    op.create_index("ix_topic_conversations_learner_created", "topic_conversations", ["learner_id", "created_at"])
    op.create_table(
        "practice_observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("content_version", sa.String(64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.Column("failed_refs", postgresql.JSONB(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id", "source", "request_id"),
    )
    op.create_index("ix_practice_observations_learner_stage_created", "practice_observations",
                    ["learner_id", "stage_id", "created_at"])
    op.create_table(
        "coach_plan_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column("history_version", sa.String(64), nullable=False),
        sa.Column("policy_version", sa.String(40), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _learner(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("learner_id", "request_id"),
    )
    op.create_index("ix_coach_plan_requests_cache", "coach_plan_requests",
                    ["learner_id", "stage_id", "history_version", "policy_version"])
    op.create_table(
        "content_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("stage_id", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(60), nullable=False),
        sa.Column("content_version", sa.String(64), nullable=False),
        sa.Column("policy_version", sa.String(60), nullable=False),
        sa.Column("model_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["learners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("cache_key"),
    )


def downgrade() -> None:
    op.drop_table("content_reviews")
    op.drop_index("ix_coach_plan_requests_cache", table_name="coach_plan_requests")
    op.drop_table("coach_plan_requests")
    op.drop_index("ix_practice_observations_learner_stage_created", table_name="practice_observations")
    op.drop_table("practice_observations")
    op.drop_index("ix_topic_conversations_learner_created", table_name="topic_conversations")
    op.drop_table("topic_conversations")
