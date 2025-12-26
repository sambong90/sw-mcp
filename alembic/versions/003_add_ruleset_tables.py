"""add ruleset tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # ruleset_versions
    op.create_table(
        'ruleset_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('effective_date', sa.String(length=20), nullable=False),
        sa.Column('rules_json', sa.Text(), nullable=False),
        sa.Column('sources_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_tag')
    )
    op.create_index('idx_ruleset_versions_version_tag', 'ruleset_versions', ['version_tag'], unique=True)
    
    # current_ruleset
    op.create_table(
        'current_ruleset',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_tag')
    )


def downgrade():
    op.drop_table('current_ruleset')
    op.drop_index('idx_ruleset_versions_version_tag', table_name='ruleset_versions')
    op.drop_table('ruleset_versions')

