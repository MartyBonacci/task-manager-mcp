"""Add calendar integration fields to tasks

Revision ID: a13ddfd17fa8
Revises: 87c34d4c9d73
Create Date: 2025-12-28 19:06:29.895891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a13ddfd17fa8'
down_revision: Union[str, Sequence[str], None] = '87c34d4c9d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add calendar integration fields to tasks table
    op.add_column('tasks', sa.Column('calendar_event_id', sa.String(length=255), nullable=True))
    op.add_column('tasks', sa.Column('calendar_event_url', sa.String(length=500), nullable=True))
    op.add_column('tasks', sa.Column('scheduled_start', sa.String(length=50), nullable=True))
    op.add_column('tasks', sa.Column('scheduled_duration', sa.Integer(), nullable=True))

    # Create indexes for calendar fields
    op.create_index(op.f('ix_tasks_calendar_event_id'), 'tasks', ['calendar_event_id'], unique=False)
    op.create_index(op.f('ix_tasks_scheduled_start'), 'tasks', ['scheduled_start'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_tasks_scheduled_start'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_calendar_event_id'), table_name='tasks')

    # Drop calendar integration columns
    op.drop_column('tasks', 'scheduled_duration')
    op.drop_column('tasks', 'scheduled_start')
    op.drop_column('tasks', 'calendar_event_url')
    op.drop_column('tasks', 'calendar_event_id')
