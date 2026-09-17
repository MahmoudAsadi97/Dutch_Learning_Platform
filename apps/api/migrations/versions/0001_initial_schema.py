"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-09-17 15:32:10.226979+00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=60), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('idempotency_key', sa.String(length=120), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('max_attempts', sa.Integer(), nullable=False),
    sa.Column('run_after', sa.DateTime(timezone=True), nullable=False),
    sa.Column('lease_owner', sa.String(length=120), nullable=False),
    sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=False),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_jobs')),
    sa.UniqueConstraint('idempotency_key', name=op.f('uq_jobs_idempotency_key'))
    )
    op.create_index('ix_jobs_status_run_after', 'jobs', ['status', 'run_after'], unique=False)
    op.create_table('learners',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('display_name', sa.String(length=200), nullable=False),
    sa.Column('identity_provider', sa.String(length=40), nullable=False),
    sa.Column('support_language', sa.String(length=10), nullable=False),
    sa.Column('target_language', sa.String(length=10), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learners')),
    sa.UniqueConstraint('email', name=op.f('uq_learners_email')),
    sa.UniqueConstraint('subject', name=op.f('uq_learners_subject'))
    )
    op.create_table('missions',
    sa.Column('id', sa.String(length=80), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('cefr_target', sa.String(length=5), nullable=False),
    sa.Column('title_nl', sa.String(length=200), nullable=False),
    sa.Column('title_fa', sa.String(length=200), nullable=False),
    sa.Column('review_status', sa.String(length=20), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('document', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('fixed_word_count', sa.Integer(), nullable=False),
    sa.Column('loaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_missions'))
    )
    op.create_table('pricing_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('sku', sa.String(length=120), nullable=False),
    sa.Column('metric', sa.String(length=30), nullable=False),
    sa.Column('unit', sa.String(length=40), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=12, scale=6), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('effective_from', sa.Date(), nullable=False),
    sa.Column('source', sa.String(length=300), nullable=False),
    sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pricing_entries')),
    sa.UniqueConstraint('provider', 'sku', 'effective_from', name='uq_pricing_entries_sku')
    )
    op.create_table('audio_assets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learner_id', sa.UUID(), nullable=True),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('blob_key', sa.String(length=300), nullable=False),
    sa.Column('container', sa.String(length=80), nullable=False),
    sa.Column('source_container_format', sa.String(length=40), nullable=False),
    sa.Column('source_codec', sa.String(length=40), nullable=False),
    sa.Column('source_bytes', sa.Integer(), nullable=False),
    sa.Column('duration_seconds', sa.Float(), nullable=False),
    sa.Column('sample_rate', sa.Integer(), nullable=False),
    sa.Column('channels', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=60), nullable=False),
    sa.Column('provider', sa.String(length=60), nullable=False),
    sa.Column('request_id', sa.String(length=64), nullable=False),
    sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], name=op.f('fk_audio_assets_learner_id_learners'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audio_assets')),
    sa.UniqueConstraint('blob_key', name=op.f('uq_audio_assets_blob_key'))
    )
    op.create_table('mission_steps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('mission_id', sa.String(length=80), nullable=False),
    sa.Column('key', sa.String(length=80), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('skill', sa.String(length=20), nullable=False),
    sa.Column('step_type', sa.String(length=20), nullable=False),
    sa.Column('variant', sa.String(length=20), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], name=op.f('fk_mission_steps_mission_id_missions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mission_steps')),
    sa.UniqueConstraint('mission_id', 'key', name='uq_mission_steps_mission_key')
    )
    op.create_table('practice_sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learner_id', sa.UUID(), nullable=False),
    sa.Column('mission_id', sa.String(length=80), nullable=False),
    sa.Column('variant', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('current_step_key', sa.String(length=80), nullable=False),
    sa.Column('request_id', sa.String(length=64), nullable=False),
    sa.Column('state', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], name=op.f('fk_practice_sessions_learner_id_learners'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], name=op.f('fk_practice_sessions_mission_id_missions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_practice_sessions')),
    sa.UniqueConstraint('learner_id', 'request_id', name='uq_practice_sessions_learner_request')
    )
    op.create_index('ix_practice_sessions_learner_status', 'practice_sessions', ['learner_id', 'status'], unique=False)
    op.create_table('skill_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learner_id', sa.UUID(), nullable=False),
    sa.Column('mission_id', sa.String(length=80), nullable=False),
    sa.Column('skill', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('latest_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('evidence_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], name=op.f('fk_skill_records_learner_id_learners'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], name=op.f('fk_skill_records_mission_id_missions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_records')),
    sa.UniqueConstraint('learner_id', 'mission_id', 'skill', name='uq_skill_records_learner_mission_skill')
    )
    op.create_table('usage_counters',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learner_id', sa.UUID(), nullable=False),
    sa.Column('scope', sa.String(length=10), nullable=False),
    sa.Column('period_key', sa.Date(), nullable=False),
    sa.Column('metric', sa.String(length=30), nullable=False),
    sa.Column('used', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('reserved', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('limit_value', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], name=op.f('fk_usage_counters_learner_id_learners'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usage_counters')),
    sa.UniqueConstraint('learner_id', 'scope', 'period_key', 'metric', name='uq_usage_counters_key')
    )
    op.create_table('usage_reservations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learner_id', sa.UUID(), nullable=False),
    sa.Column('metric', sa.String(length=30), nullable=False),
    sa.Column('request_id', sa.String(length=64), nullable=False),
    sa.Column('amount_reserved', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('amount_used', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('state', sa.String(length=12), nullable=False),
    sa.Column('period_key', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], name=op.f('fk_usage_reservations_learner_id_learners'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usage_reservations')),
    sa.UniqueConstraint('learner_id', 'metric', 'request_id', name='uq_usage_reservations_request')
    )
    op.create_table('practice_turns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('turn_index', sa.Integer(), nullable=False),
    sa.Column('step_key', sa.String(length=80), nullable=False),
    sa.Column('request_id', sa.String(length=64), nullable=False),
    sa.Column('modality', sa.String(length=20), nullable=False),
    sa.Column('learner_text', sa.Text(), nullable=False),
    sa.Column('learner_audio_asset_id', sa.UUID(), nullable=True),
    sa.Column('character_text', sa.Text(), nullable=False),
    sa.Column('character_audio_asset_id', sa.UUID(), nullable=True),
    sa.Column('proposed_action', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('action_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('model_meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['character_audio_asset_id'], ['audio_assets.id'], name=op.f('fk_practice_turns_character_audio_asset_id_audio_assets'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['learner_audio_asset_id'], ['audio_assets.id'], name=op.f('fk_practice_turns_learner_audio_asset_id_audio_assets'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_id'], ['practice_sessions.id'], name=op.f('fk_practice_turns_session_id_practice_sessions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_practice_turns')),
    sa.UniqueConstraint('session_id', 'request_id', name='uq_practice_turns_session_request'),
    sa.UniqueConstraint('session_id', 'turn_index', name='uq_practice_turns_session_index')
    )
    op.create_table('evidence_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('turn_id', sa.UUID(), nullable=True),
    sa.Column('step_key', sa.String(length=80), nullable=False),
    sa.Column('skill', sa.String(length=20), nullable=False),
    sa.Column('kind', sa.String(length=40), nullable=False),
    sa.Column('modality', sa.String(length=20), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['practice_sessions.id'], name=op.f('fk_evidence_records_session_id_practice_sessions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['turn_id'], ['practice_turns.id'], name=op.f('fk_evidence_records_turn_id_practice_turns'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_evidence_records'))
    )
    op.create_index('ix_evidence_records_session_skill', 'evidence_records', ['session_id', 'skill'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_evidence_records_session_skill', table_name='evidence_records')
    op.drop_table('evidence_records')
    op.drop_table('practice_turns')
    op.drop_table('usage_reservations')
    op.drop_table('usage_counters')
    op.drop_table('skill_records')
    op.drop_index('ix_practice_sessions_learner_status', table_name='practice_sessions')
    op.drop_table('practice_sessions')
    op.drop_table('mission_steps')
    op.drop_table('audio_assets')
    op.drop_table('pricing_entries')
    op.drop_table('missions')
    op.drop_table('learners')
    op.drop_index('ix_jobs_status_run_after', table_name='jobs')
    op.drop_table('jobs')
