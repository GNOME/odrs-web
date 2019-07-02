"""

Revision ID: 84deb10331db
Revises: bbbcd54c69ac
Create Date: 2019-07-02 10:26:30.036790

"""

# revision identifiers, used by Alembic.
revision = '84deb10331db'
down_revision = 'bbbcd54c69ac'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.alter_column('users', 'user_hash',
               existing_type=mysql.TEXT(),
               type_=sa.String(length=40),
               existing_nullable=True)


def downgrade():
    op.alter_column('users', 'user_hash',
               existing_type=sa.String(length=40),
               type_=mysql.TEXT(),
               existing_nullable=True)
