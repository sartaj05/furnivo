"""add accounting, branch, routing, and service execution fields

Revision ID: f5a8c4d12e60
Revises: e4f7a2c91b30
Create Date: 2026-09-23 16:20:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'f5a8c4d12e60'
down_revision = 'e4f7a2c91b30'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=160), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('manager', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('code'), sa.UniqueConstraint('name'))
    op.create_table('user_branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('user_id', 'branch_id', name='uq_user_branch'))
    op.create_index('ix_user_branches_user_id', 'user_branches', ['user_id'])
    op.create_index('ix_user_branches_branch_id', 'user_branches', ['branch_id'])
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('branch_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_warehouses_branch_id', ['branch_id'])
        batch_op.create_foreign_key('fk_warehouses_branch_id', 'branches', ['branch_id'], ['id'])
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('accounting_status', sa.String(length=40), nullable=False, server_default='Pending'))
        batch_op.add_column(sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('delivery_schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('driver_name', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('driver_phone', sa.String(length=60), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('route_order', sa.Integer(), nullable=False, server_default='0'))
    with op.batch_alter_table('service_tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('visit_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('parts_used', sa.Text(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('technician_minutes', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('customer_rating', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('customer_feedback', sa.Text(), nullable=False, server_default=''))


def downgrade():
    with op.batch_alter_table('service_tickets', schema=None) as batch_op:
        for column in ('customer_feedback', 'customer_rating', 'technician_minutes', 'parts_used', 'visit_date'): batch_op.drop_column(column)
    with op.batch_alter_table('delivery_schedules', schema=None) as batch_op:
        for column in ('route_order', 'driver_phone', 'driver_name'): batch_op.drop_column(column)
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_column('reminder_sent_at'); batch_op.drop_column('accounting_status')
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_warehouses_branch_id', type_='foreignkey'); batch_op.drop_index('ix_warehouses_branch_id'); batch_op.drop_column('branch_id')
    op.drop_index('ix_user_branches_branch_id', table_name='user_branches'); op.drop_index('ix_user_branches_user_id', table_name='user_branches'); op.drop_table('user_branches'); op.drop_table('branches')
