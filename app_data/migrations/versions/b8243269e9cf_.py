"""

Revision ID: b8243269e9cf
Revises: None
Create Date: 2019-06-28 12:39:37.287224

"""

# revision identifiers, used by Alembic.
revision = 'b8243269e9cf'
down_revision = None

from alembic import op
import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from odrs import db
from odrs.models import Review

def upgrade():
    op.alter_column('reviews', 'date_deleted',
               existing_type=mysql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text("'0000-00-00 00:00:00'"))
    since = datetime.datetime.now() - datetime.timedelta(hours=3)
    for review in db.session.query(Review).all():
        if review.date_deleted == '0000-00-00 00:00:00':
             review.date_deleted = None
        if review.date_deleted > since:
             review.date_deleted = None

    db.session.commit()


def downgrade():
    op.alter_column('reviews', 'date_deleted',
               existing_type=mysql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text("'0000-00-00 00:00:00'"))
