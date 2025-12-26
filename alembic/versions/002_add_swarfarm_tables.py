"""add swarfarm ingestion tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # swarfarm_raw
    op.create_table(
        'swarfarm_raw',
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('com2us_id', sa.Integer(), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('endpoint', 'object_id', name='uq_swarfarm_raw_endpoint_object')
    )
    op.create_index('idx_swarfarm_raw_endpoint', 'swarfarm_raw', ['endpoint'], unique=False)
    op.create_index('idx_swarfarm_raw_com2us_id', 'swarfarm_raw', ['com2us_id'], unique=False)
    op.create_index('idx_swarfarm_raw_payload_hash', 'swarfarm_raw', ['payload_hash'], unique=False)
    
    # swarfarm_sync_state
    op.create_table(
        'swarfarm_sync_state',
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('list_url', sa.String(length=500), nullable=False),
        sa.Column('etag', sa.String(length=200), nullable=True),
        sa.Column('last_modified', sa.String(length=200), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_count', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('endpoint')
    )
    
    # swarfarm_change_log
    op.create_table(
        'swarfarm_change_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('old_hash', sa.String(length=64), nullable=True),
        sa.Column('new_hash', sa.String(length=64), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("change_type IN ('insert', 'update')", name='chk_change_type')
    )
    op.create_index('idx_swarfarm_change_log_endpoint', 'swarfarm_change_log', ['endpoint'], unique=False)
    op.create_index('idx_swarfarm_change_log_object_id', 'swarfarm_change_log', ['object_id'], unique=False)
    
    # swarfarm_snapshot
    op.create_table(
        'swarfarm_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('endpoints_total', sa.Integer(), nullable=False),
        sa.Column('endpoints_changed', sa.Integer(), nullable=False),
        sa.Column('endpoints_304', sa.Integer(), nullable=False),
        sa.Column('objects_inserted', sa.Integer(), nullable=False),
        sa.Column('objects_updated', sa.Integer(), nullable=False),
        sa.Column('objects_unchanged', sa.Integer(), nullable=False),
        sa.Column('errors_total', sa.Integer(), nullable=False),
        sa.Column('summary_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('swarfarm_snapshot')
    op.drop_index('idx_swarfarm_change_log_object_id', table_name='swarfarm_change_log')
    op.drop_index('idx_swarfarm_change_log_endpoint', table_name='swarfarm_change_log')
    op.drop_table('swarfarm_change_log')
    op.drop_table('swarfarm_sync_state')
    op.drop_index('idx_swarfarm_raw_payload_hash', table_name='swarfarm_raw')
    op.drop_index('idx_swarfarm_raw_com2us_id', table_name='swarfarm_raw')
    op.drop_index('idx_swarfarm_raw_endpoint', table_name='swarfarm_raw')
    op.drop_table('swarfarm_raw')

