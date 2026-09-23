"""add production scheduling and quality inspection tables

Revision ID: g6b9d5e23f71
Revises: f5a8c4d12e60
Create Date: 2026-09-23 17:20:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'g6b9d5e23f71'
down_revision = 'f5a8c4d12e60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('production_tasks',
        sa.Column('id', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('production_job_id', sa.Integer(), nullable=False), sa.Column('name', sa.String(length=160), nullable=False), sa.Column('stage', sa.String(length=60), nullable=False), sa.Column('assigned_worker', sa.String(length=120), nullable=False), sa.Column('machine', sa.String(length=120), nullable=False), sa.Column('dependency_id', sa.Integer(), nullable=True), sa.Column('planned_start', sa.DateTime(timezone=True), nullable=True), sa.Column('planned_end', sa.DateTime(timezone=True), nullable=True), sa.Column('actual_minutes', sa.Integer(), nullable=False), sa.Column('status', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['dependency_id'], ['production_tasks.id']), sa.ForeignKeyConstraint(['production_job_id'], ['production_jobs.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_production_tasks_production_job_id', 'production_tasks', ['production_job_id'])
    op.create_table('quality_inspections',
        sa.Column('id', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('production_job_id', sa.Integer(), nullable=False), sa.Column('inspector_id', sa.Integer(), nullable=False), sa.Column('status', sa.String(length=40), nullable=False), sa.Column('checklist_json', sa.Text(), nullable=False), sa.Column('defects_json', sa.Text(), nullable=False), sa.Column('photo_url', sa.String(length=500), nullable=False), sa.Column('notes', sa.Text(), nullable=False), sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id']), sa.ForeignKeyConstraint(['production_job_id'], ['production_jobs.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_quality_inspections_production_job_id', 'quality_inspections', ['production_job_id'])


def downgrade():
    op.drop_index('ix_quality_inspections_production_job_id', table_name='quality_inspections'); op.drop_table('quality_inspections')
    op.drop_index('ix_production_tasks_production_job_id', table_name='production_tasks'); op.drop_table('production_tasks')
