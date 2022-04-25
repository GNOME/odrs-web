"""

Revision ID: 036f0cd034e5
Revises: b63a028c3346
Create Date: 2019-07-03 11:39:22.323579

"""

# revision identifiers, used by Alembic.
revision = "036f0cd034e5"
down_revision = "b63a028c3346"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_foreign_key(None, "votes", "reviews", ["review_id"], ["review_id"])


def downgrade():
    op.drop_constraint(None, "votes", type_="foreignkey")
