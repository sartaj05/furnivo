"""add staff invitations

Revision ID: k2f8a1c3d5e7
Revises: j9e2b8c56d04
"""

from alembic import op
import sqlalchemy as sa


revision = 'k2f8a1c3d5e7'
down_revision = 'j9e2b8c56d04'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if 'staff_invitations' not in inspector.get_table_names():
        op.create_table(
            'staff_invitations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=30), nullable=False, server_default='sales'),
            sa.Column('token_hash', sa.String(length=128), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('invited_by_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['invited_by_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token_hash'),
        )
    indexes = {index['name'] for index in sa.inspect(op.get_bind()).get_indexes('staff_invitations')}
    if 'ix_staff_invitations_email' not in indexes:
        op.create_index('ix_staff_invitations_email', 'staff_invitations', ['email'], unique=False)
    if 'ix_staff_invitations_token_hash' not in indexes:
        op.create_index('ix_staff_invitations_token_hash', 'staff_invitations', ['token_hash'], unique=False)


def downgrade():
    if 'staff_invitations' in sa.inspect(op.get_bind()).get_table_names():
        op.drop_index('ix_staff_invitations_token_hash', table_name='staff_invitations')
        op.drop_index('ix_staff_invitations_email', table_name='staff_invitations')
        op.drop_table('staff_invitations')
