"""add monsters table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'monsters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('name_ko', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('element', sa.String(length=20), nullable=False),
        sa.Column('awakened', sa.Boolean(), nullable=True),
        sa.Column('nat_stars', sa.Integer(), nullable=False),
        sa.Column('base_hp', sa.Integer(), nullable=False),
        sa.Column('base_atk', sa.Integer(), nullable=False),
        sa.Column('base_def', sa.Integer(), nullable=False),
        sa.Column('base_spd', sa.Integer(), nullable=False),
        sa.Column('base_cr', sa.Integer(), nullable=True),
        sa.Column('base_cd', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('master_id')
    )
    op.create_index(op.f('ix_monsters_master_id'), 'monsters', ['master_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_monsters_master_id'), table_name='monsters')
    op.drop_table('monsters')

