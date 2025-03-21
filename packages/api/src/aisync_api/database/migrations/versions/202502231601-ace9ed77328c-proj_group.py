"""proj group

Revision ID: ace9ed77328c
Revises: f1a4dd538cc2
Create Date: 2025-02-23 16:01:45.223976

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ace9ed77328c"
down_revision: Union[str, None] = "f1a4dd538cc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "proj_team",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "proj_project",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["proj_team.id"], name="fk_project_team"),
        sa.ForeignKeyConstraint(["user_id"], ["auth_user.id"], name="fk_project_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("auth_user_role", sa.Column("team_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_user_role_team", "auth_user_role", "proj_team", ["team_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_user_role_team", "auth_user_role", type_="foreignkey")
    op.drop_column("auth_user_role", "team_id")
    op.drop_table("proj_project")
    op.drop_table("proj_team")
    # ### end Alembic commands ###
