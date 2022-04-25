"""

Revision ID: bbbcd54c69ac
Revises: 1b966aab67a1
Create Date: 2019-07-02 10:06:20.015220

"""

# revision identifiers, used by Alembic.
revision = "bbbcd54c69ac"
down_revision = "1b966aab67a1"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.alter_column(
        "eventlog",
        "important",
        existing_type=mysql.INTEGER(display_width=11),
        type_=sa.Boolean(),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "moderators",
        "is_admin",
        existing_type=mysql.TINYINT(display_width=4),
        type_=sa.Boolean(),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "moderators",
        "is_enabled",
        existing_type=mysql.TINYINT(display_width=4),
        type_=sa.Boolean(),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "users",
        "is_banned",
        existing_type=mysql.INTEGER(display_width=11),
        type_=sa.Boolean(),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )


def downgrade():
    op.alter_column(
        "users",
        "is_banned",
        existing_type=sa.Boolean(),
        type_=mysql.INTEGER(display_width=11),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "moderators",
        "is_enabled",
        existing_type=sa.Boolean(),
        type_=mysql.TINYINT(display_width=4),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "moderators",
        "is_admin",
        existing_type=sa.Boolean(),
        type_=mysql.TINYINT(display_width=4),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
    op.alter_column(
        "eventlog",
        "important",
        existing_type=sa.Boolean(),
        type_=mysql.INTEGER(display_width=11),
        existing_nullable=True,
        existing_server_default=sa.text("0"),
    )
