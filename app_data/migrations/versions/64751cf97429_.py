"""

Revision ID: 64751cf97429
Revises: 036f0cd034e5
Create Date: 2019-07-03 14:24:53.549481

"""

# revision identifiers, used by Alembic.
revision = '64751cf97429'
down_revision = '036f0cd034e5'

from odrs import db
from odrs.models import Review
from odrs.util import _addr_hash

def upgrade():
    for review in db.session.query(Review).all():
        review.user_addr = _addr_hash(review.user_addr_hash)
    db.session.commit()

def downgrade():
    pass
