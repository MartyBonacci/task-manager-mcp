"""Create initial OAuth 2.1 schema

Revision ID: 87c34d4c9d73
Revises: 
Create Date: 2025-12-26 12:22:33.537748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87c34d4c9d73'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table first (no dependencies)
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create dynamic_clients table (no dependencies)
    op.create_table(
        'dynamic_clients',
        sa.Column('client_id', sa.String(length=36), nullable=False),
        sa.Column('client_secret', sa.LargeBinary(length=512), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('redirect_uris', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('client_id')
    )
    op.create_index('idx_dynamic_client_expires_at', 'dynamic_clients', ['expires_at'], unique=False)
    op.create_index('idx_dynamic_client_platform', 'dynamic_clients', ['platform'], unique=False)

    # Create tasks table (depends on users)
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('project', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('energy', sa.String(length=20), nullable=False),
        sa.Column('time_estimate', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('due_date', sa.String(length=50), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_tasks_project'), 'tasks', ['project'], unique=False)
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_tasks_completed'), 'tasks', ['completed'], unique=False)

    # Create sessions table (depends on users)
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(length=43), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('access_token', sa.LargeBinary(length=512), nullable=False),
        sa.Column('refresh_token', sa.LargeBinary(length=512), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('idx_session_user_id', 'sessions', ['user_id'], unique=False)
    op.create_index('idx_session_expires_at', 'sessions', ['expires_at'], unique=False)
    op.create_index('idx_session_last_activity', 'sessions', ['last_activity'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (tables with FK constraints first)
    op.drop_index('idx_session_last_activity', table_name='sessions')
    op.drop_index('idx_session_expires_at', table_name='sessions')
    op.drop_index('idx_session_user_id', table_name='sessions')
    op.drop_table('sessions')

    op.drop_index(op.f('ix_tasks_completed'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_due_date'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_priority'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_project'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index('idx_dynamic_client_platform', table_name='dynamic_clients')
    op.drop_index('idx_dynamic_client_expires_at', table_name='dynamic_clients')
    op.drop_table('dynamic_clients')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
