"""Activity events: one append-only row per countable learner action; the day keeps its goal.

Every point now comes from an event, so a day's points equal the sum of its events. Days recorded before
this table get one `legacy` event carrying their points.

Revision ID: 0009
Revises: 0008
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("ref", sa.String(200), nullable=False),
        sa.Column("dedupe_key", sa.String(240), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("skill", sa.String(20), nullable=True),
        sa.Column("request_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], name="fk_activity_events_learner_id_learners",
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_activity_events"),
        sa.UniqueConstraint("learner_id", "kind", "dedupe_key", name="uq_activity_events_learner_id"),
    )
    op.create_index("ix_activity_events_learner_day", "activity_events", ["learner_id", "day"])
    op.add_column("learning_days", sa.Column("goal_target", sa.Integer(), nullable=True))
    op.add_column("learning_days", sa.Column("exercise_items", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("learning_days", sa.Column("exercise_sessions", sa.Integer(), nullable=False, server_default="0"))
    op.execute(
        """
        INSERT INTO activity_events (id, learner_id, kind, ref, dedupe_key, day, points, units, skill, request_id,
                                     meta, created_at)
        SELECT gen_random_uuid(), learner_id, 'legacy', day::text, day::text, day, points, 0, NULL, '',
               '{}'::jsonb, updated_at
        FROM learning_days
        WHERE points > 0
        """
    )


def downgrade() -> None:
    op.drop_column("learning_days", "exercise_sessions")
    op.drop_column("learning_days", "exercise_items")
    op.drop_column("learning_days", "goal_target")
    op.drop_index("ix_activity_events_learner_day", table_name="activity_events")
    op.drop_table("activity_events")
