"""add invoice workflow fields

Revision ID: b7f0c8d4e912
Revises: 81944cbe44fa
Create Date: 2026-09-23 11:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7f0c8d4e912'
down_revision = '81944cbe44fa'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_type', sa.String(length=30), nullable=False, server_default='Final'))
        batch_op.add_column(sa.Column('deposit_percent', sa.Numeric(6, 2), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_column('deposit_percent')
        batch_op.drop_column('invoice_type')
