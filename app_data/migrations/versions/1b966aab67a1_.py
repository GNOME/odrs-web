"""

Revision ID: 1b966aab67a1
Revises: fd438e12c80c
Create Date: 2019-07-01 19:44:32.916028

"""

# revision identifiers, used by Alembic.
revision = '1b966aab67a1'
down_revision = 'b8243269e9cf'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from odrs import db

class OldModerator(db.Model):
    __tablename__ = 'moderators'
    __table_args__ = {'mysql_character_set': 'utf8mb4',
                      'extend_existing': True}
    email = db.Column(db.Text)

def upgrade():
    for mod in db.session.query(OldModerator).all():
        mod.username = mod.email
    db.session.commit()
    op.drop_column('moderators', 'email')

def downgrade():
    op.add_column('moderators', sa.Column('email', mysql.MEDIUMTEXT(collation='utf8mb4_unicode_ci'), nullable=True))
