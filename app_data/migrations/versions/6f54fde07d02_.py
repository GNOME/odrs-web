"""

Revision ID: 6f54fde07d02
Revises: e6fa15874247
Create Date: 2019-07-04 11:58:24.685366

"""

# revision identifiers, used by Alembic.
revision = '6f54fde07d02'
down_revision = 'e6fa15874247'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import InternalError

from odrs import db
from odrs.models import Analytic, Component

def upgrade():
    try:
        op.add_column('components', sa.Column('fetch_cnt', sa.Integer(), nullable=True))
    except InternalError as e:
        print(str(e))
    for component in db.session.query(Component).\
                        filter(Component.app_id != '').\
                        order_by(Component.app_id.asc()).all():
        fetch_cnt = 0
        for val in db.session.query(Analytic.fetch_cnt).\
                        filter(Analytic.app_id == component.app_id).all():
            fetch_cnt += val[0]
        component.fetch_cnt = fetch_cnt
        print(component.app_id, fetch_cnt)
    db.session.commit()

def downgrade():
    op.drop_column('components', 'fetch_cnt')
