"""add AI analytics and multi-tenant SaaS foundations

Revision ID: h7c0e6f34a82
Revises: g6b9d5e23f71
Create Date: 2026-09-23 18:15:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'h7c0e6f34a82'
down_revision = 'g6b9d5e23f71'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('tenants', sa.Column('id', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.Column('name', sa.String(length=180), nullable=False), sa.Column('slug', sa.String(length=100), nullable=False), sa.Column('plan', sa.String(length=40), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('branding_json', sa.Text(), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('slug'))
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])
    op.create_table('tenant_memberships', sa.Column('id', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.Column('tenant_id', sa.Integer(), nullable=False), sa.Column('user_id', sa.Integer(), nullable=False), sa.Column('role', sa.String(length=40), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'), sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'))
    op.create_index('ix_tenant_memberships_tenant_id', 'tenant_memberships', ['tenant_id']); op.create_index('ix_tenant_memberships_user_id', 'tenant_memberships', ['user_id'])
    op.create_table('subscriptions', sa.Column('id', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.Column('tenant_id', sa.Integer(), nullable=False), sa.Column('provider', sa.String(length=40), nullable=False), sa.Column('external_id', sa.String(length=180), nullable=False), sa.Column('plan', sa.String(length=40), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('seats', sa.Integer(), nullable=False), sa.Column('monthly_amount', sa.Numeric(12, 2), nullable=False), sa.Column('current_period_end', sa.Date(), nullable=True), sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('tenant_id'))
    with op.batch_alter_table('users', schema=None) as batch_op: batch_op.add_column(sa.Column('active_tenant_id', sa.Integer(), nullable=True)); batch_op.create_index('ix_users_active_tenant_id', ['active_tenant_id']); batch_op.create_foreign_key('fk_users_active_tenant_id', 'tenants', ['active_tenant_id'], ['id'])
    with op.batch_alter_table('quality_inspections', schema=None) as batch_op: batch_op.add_column(sa.Column('rework_cost', sa.Numeric(12, 2), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('quality_inspections', schema=None) as batch_op: batch_op.drop_column('rework_cost')
    with op.batch_alter_table('users', schema=None) as batch_op: batch_op.drop_constraint('fk_users_active_tenant_id', type_='foreignkey'); batch_op.drop_index('ix_users_active_tenant_id'); batch_op.drop_column('active_tenant_id')
    op.drop_table('subscriptions'); op.drop_index('ix_tenant_memberships_user_id', table_name='tenant_memberships'); op.drop_index('ix_tenant_memberships_tenant_id', table_name='tenant_memberships'); op.drop_table('tenant_memberships'); op.drop_index('ix_tenants_slug', table_name='tenants'); op.drop_table('tenants')
