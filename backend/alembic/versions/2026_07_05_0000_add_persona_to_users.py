"""Add persona column to users table.

Revision ID: 202607050000
Revises: 43290495852e
Create Date: 2026-07-05 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '202607050000'
down_revision: Union[str, None] = '43290495852e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.add_column('users', sa.Column('persona', sa.Text(), nullable=True))
    op.alter_column('users', 'persona', comment='User persona/preferences for personalized responses')


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column('users', 'persona')
