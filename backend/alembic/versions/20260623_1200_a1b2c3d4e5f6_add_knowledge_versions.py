"""add knowledge_versions + result version tags

Revision ID: a1b2c3d4e5f6
Revises: f7ed8dd3ea71
Create Date: 2026-06-23 12:00:00.000000+00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f7ed8dd3ea71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'knowledge_versions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('summary', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_knowledge_versions_organization_id'), 'knowledge_versions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_knowledge_versions_version_number'), 'knowledge_versions', ['version_number'], unique=False)

    op.add_column('interaction_llm_trigger_cache', sa.Column('knowledge_version', sa.Integer(), nullable=True))
    op.add_column('policy_compliance', sa.Column('knowledge_version', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('policy_compliance', 'knowledge_version')
    op.drop_column('interaction_llm_trigger_cache', 'knowledge_version')

    op.drop_index(op.f('ix_knowledge_versions_version_number'), table_name='knowledge_versions')
    op.drop_index(op.f('ix_knowledge_versions_organization_id'), table_name='knowledge_versions')
    op.drop_table('knowledge_versions')
