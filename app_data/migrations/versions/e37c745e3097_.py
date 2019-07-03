"""

Revision ID: e37c745e3097
Revises: 64751cf97429
Create Date: 2019-07-03 19:54:01.718718

"""

# revision identifiers, used by Alembic.
revision = 'e37c745e3097'
down_revision = '64751cf97429'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_table('taboos',
    sa.Column('taboo_id', sa.Integer(), nullable=False),
    sa.Column('locale', sa.String(length=8), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('taboo_id'),
    sa.UniqueConstraint('taboo_id'),
    mysql_character_set='utf8mb4'
    )
    op.create_index(op.f('ix_taboos_locale'), 'taboos', ['locale'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_taboos_locale'), table_name='taboos')
    op.drop_table('taboos')
