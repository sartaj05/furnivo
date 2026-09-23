"""add execution, procurement, and delivery workflow fields

Revision ID: e4f7a2c91b30
Revises: d9e2b8f3a416
Create Date: 2026-09-23 15:10:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'e4f7a2c91b30'
down_revision = 'd9e2b8f3a416'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('field_visits', schema=None) as batch_op:
        batch_op.add_column(sa.Column('check_in_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('check_out_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('time_minutes', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('materials_json', sa.Text(), nullable=False, server_default='[]'))
    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supplier_quote_ref', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('actual_delivery_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('landed_cost', sa.Numeric(12, 2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('quality_rating', sa.Numeric(3, 1), nullable=False, server_default='0'))
    with op.batch_alter_table('delivery_schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('eta', sa.String(length=80), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('customer_confirmed', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('delivery_schedules', schema=None) as batch_op:
        batch_op.drop_column('customer_confirmed')
        batch_op.drop_column('eta')
    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.drop_column('quality_rating')
        batch_op.drop_column('landed_cost')
        batch_op.drop_column('actual_delivery_date')
        batch_op.drop_column('supplier_quote_ref')
    with op.batch_alter_table('field_visits', schema=None) as batch_op:
        batch_op.drop_column('materials_json')
        batch_op.drop_column('time_minutes')
        batch_op.drop_column('check_out_at')
        batch_op.drop_column('check_in_at')
