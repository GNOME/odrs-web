"""

Revision ID: b2d75ba212ed
Revises: e37c745e3097
Create Date: 2019-07-04 09:07:17.032627

"""

# revision identifiers, used by Alembic.
revision = 'b2d75ba212ed'
down_revision = 'e37c745e3097'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('taboos', sa.Column('severity', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('taboos', 'severity')
