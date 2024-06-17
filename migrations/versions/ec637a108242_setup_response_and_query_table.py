"""Setup response and query table

Revision ID: ec637a108242
Revises: 21f3364b195b
Create Date: 2024-06-17 12:21:45.015767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'ec637a108242'
down_revision: Union[str, None] = '21f3364b195b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.create_table('query_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('embedding', Vector(dim=1024), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('response_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('embedding', Vector(dim=1024), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('response_logs')
    op.drop_table('query_logs')
    # ### end Alembic commands ###
