"""add product and BOM costing fields

Revision ID: d9e2b8f3a416
Revises: c4d9a7e1f205
Create Date: 2026-09-23 13:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'd9e2b8f3a416'
down_revision = 'c4d9a7e1f205'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_price', sa.Numeric(12, 2), nullable=False, server_default='0'))
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit_cost', sa.Numeric(12, 2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('labor_cost', sa.Numeric(12, 2), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('bom_items', schema=None) as batch_op:
        batch_op.drop_column('labor_cost')
        batch_op.drop_column('unit_cost')
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('cost_price')
