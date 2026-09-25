"""add user approval limits

Revision ID: l3a9b2c4d6e8
Revises: k2f8a1c3d5e7
"""

from alembic import op
import sqlalchemy as sa


revision = 'l3a9b2c4d6e8'
down_revision = 'k2f8a1c3d5e7'
branch_labels = None
depends_on = None


def upgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    if 'approval_limit' not in existing:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('approval_limit', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'))


def downgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    if 'approval_limit' in existing:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('approval_limit')
