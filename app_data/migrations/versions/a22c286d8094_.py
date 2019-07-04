"""

Revision ID: a22c286d8094
Revises: 6f54fde07d02
Create Date: 2019-07-04 13:50:13.788206

"""

# revision identifiers, used by Alembic.
revision = 'a22c286d8094'
down_revision = '6f54fde07d02'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.drop_column('reviews', 'app_id')


def downgrade():
    op.add_column('reviews', sa.Column('app_id', mysql.TEXT(), nullable=True))
