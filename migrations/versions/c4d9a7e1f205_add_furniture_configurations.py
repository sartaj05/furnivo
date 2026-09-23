"""add saved furniture configurations

Revision ID: c4d9a7e1f205
Revises: b7f0c8d4e912
Create Date: 2026-09-23 12:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'c4d9a7e1f205'
down_revision = 'b7f0c8d4e912'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'furniture_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('configuration_number', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=180), nullable=False),
        sa.Column('room', sa.String(length=120), nullable=False, server_default=''),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Saved'),
        sa.Column('items_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('configuration_number'),
    )
    op.create_index('ix_furniture_configurations_configuration_number', 'furniture_configurations', ['configuration_number'], unique=False)
    op.create_index('ix_furniture_configurations_customer_id', 'furniture_configurations', ['customer_id'], unique=False)
    op.create_index('ix_furniture_configurations_quote_id', 'furniture_configurations', ['quote_id'], unique=False)


def downgrade():
    op.drop_index('ix_furniture_configurations_quote_id', table_name='furniture_configurations')
    op.drop_index('ix_furniture_configurations_customer_id', table_name='furniture_configurations')
    op.drop_index('ix_furniture_configurations_configuration_number', table_name='furniture_configurations')
    op.drop_table('furniture_configurations')
