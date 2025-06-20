"""
create tables for models

Revision ID: 0001_create_tables
Revises:
Create Date: 2025-06-19 12:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('mentors',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('bio', sa.Text()),
        sa.Column('contact', sa.String(255)),
    )
    op.create_table('events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('datetime', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('mentor_id', sa.Integer(), sa.ForeignKey('mentors.id'), nullable=False),
    )
    op.create_table('records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('file_url', sa.String(500), nullable=False),
    )
    op.create_table('projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('required_roles', postgresql.ARRAY(sa.String())),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
    )
    op.create_table('vacancies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('link', sa.String(500), nullable=False),
    )

def downgrade():
    op.drop_table('vacancies')
    op.drop_table('projects')
    op.drop_table('records')
    op.drop_table('events')
    op.drop_table('mentors')