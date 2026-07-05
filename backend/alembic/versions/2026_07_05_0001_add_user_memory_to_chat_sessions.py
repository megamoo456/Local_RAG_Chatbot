"""Add user_memory column to chat_sessions table.

Revision ID: 202607050001
Revises: 202607050000
Create Date: 2026-07-05 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '202607050001'
down_revision: Union[str, None] = '202607050000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.add_column('chat_sessions', sa.Column('user_memory', sa.Text(), nullable=True))
    op.alter_column('chat_sessions', 'user_memory', comment='Persistent user preferences and facts for this session')


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column('chat_sessions', 'user_memory')
