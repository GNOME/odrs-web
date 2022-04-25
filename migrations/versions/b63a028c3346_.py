"""

Revision ID: b63a028c3346
Revises: 19526c284b29
Create Date: 2019-07-02 11:13:57.117376

"""

# revision identifiers, used by Alembic.
revision = "b63a028c3346"
down_revision = "19526c284b29"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.drop_column("eventlog", "user_hash")
    op.drop_column("moderators", "user_hash")
    op.drop_column("reviews", "user_hash")
    op.drop_column("votes", "user_hash")


def downgrade():
    op.add_column("votes", sa.Column("user_hash", mysql.TEXT(), nullable=True))
    op.add_column("reviews", sa.Column("user_hash", mysql.TEXT(), nullable=True))
    op.add_column("moderators", sa.Column("user_hash", mysql.TEXT(), nullable=True))
    op.add_column("eventlog", sa.Column("user_hash", mysql.TEXT(), nullable=True))
