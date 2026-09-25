"""add production to delivery handoffs

Revision ID: m4b0c3d5e7f9
Revises: l3a9b2c4d6e8
"""
from alembic import op
import sqlalchemy as sa

revision = 'm4b0c3d5e7f9'
down_revision = 'l3a9b2c4d6e8'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if 'production_handoffs' in inspector.get_table_names(): return
    op.create_table('production_handoffs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('production_job_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('handed_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False, server_default='Ready for delivery'),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('handed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['handed_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['production_job_id'], ['production_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('production_job_id'))
    op.create_index('ix_production_handoffs_production_job_id', 'production_handoffs', ['production_job_id'], unique=False)
    op.create_index('ix_production_handoffs_order_id', 'production_handoffs', ['order_id'], unique=False)


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if 'production_handoffs' not in inspector.get_table_names(): return
    op.drop_index('ix_production_handoffs_order_id', table_name='production_handoffs')
    op.drop_index('ix_production_handoffs_production_job_id', table_name='production_handoffs')
    op.drop_table('production_handoffs')
