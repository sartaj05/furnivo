"""add public contact fields to leads

Revision ID: j9e2b8c56d04
Revises: i8d1f7a45b93
"""

from alembic import op
import sqlalchemy as sa


revision = 'j9e2b8c56d04'
down_revision = 'i8d1f7a45b93'
branch_labels = None
depends_on = None


def upgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('leads')}
    with op.batch_alter_table('leads', schema=None) as batch_op:
        if 'interest' not in existing:
            batch_op.add_column(sa.Column('interest', sa.String(length=100), nullable=False, server_default='General enquiry'))
        if 'message' not in existing:
            batch_op.add_column(sa.Column('message', sa.Text(), nullable=False, server_default=''))


def downgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('leads')}
    with op.batch_alter_table('leads', schema=None) as batch_op:
        if 'message' in existing:
            batch_op.drop_column('message')
        if 'interest' in existing:
            batch_op.drop_column('interest')
