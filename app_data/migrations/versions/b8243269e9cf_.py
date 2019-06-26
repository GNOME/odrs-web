"""

Revision ID: b8243269e9cf
Revises: None
Create Date: 2019-06-28 12:39:37.287224

"""

# revision identifiers, used by Alembic.
revision = 'b8243269e9cf'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.alter_column('reviews', 'date_deleted',
               existing_type=mysql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text("'0000-00-00 00:00:00'"))


def downgrade():
    op.alter_column('reviews', 'date_deleted',
               existing_type=mysql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text("'0000-00-00 00:00:00'"))
