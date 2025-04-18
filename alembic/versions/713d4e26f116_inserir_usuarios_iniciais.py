"""inserir usuarios iniciais

Revision ID: 713d4e26f116
Revises: fb0704069a69
Create Date: 2025-04-17 17:48:47.400308

"""
from typing import Sequence, Union
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '713d4e26f116'
down_revision: Union[str, None] = 'fb0704069a69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

users_table = table('users',
    column('id', Integer),
    column('username', String),
    column('hashed_password', String)
)

def upgrade() -> None:
    # op.bulk_insert(users_table, [
    #     {"username": "admin", "hashed_password": "$2b$12$oFOvO5wZ9xbyqI4cbguAF.qoMC3tqeQn01qkk7bBXJ6jcKbbjXKqe"}
    # ])
    pass


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE username IN ('admin')")
    pass
