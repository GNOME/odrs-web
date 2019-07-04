"""

Revision ID: e6fa15874247
Revises: b2d75ba212ed
Create Date: 2019-07-04 10:44:23.739416

"""

# revision identifiers, used by Alembic.
revision = 'e6fa15874247'
down_revision = 'b2d75ba212ed'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import InternalError

from odrs import db
from odrs.models import Review, Component

def upgrade():

    try:
        op.create_table('components',
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('app_id', sa.Text(), nullable=True),
        sa.Column('review_cnt', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('component_id'),
        sa.UniqueConstraint('component_id'),
        mysql_character_set='utf8mb4'
        )
        op.add_column('reviews', sa.Column('component_id', sa.Integer(), nullable=False))
        op.create_foreign_key(None, 'reviews', 'components', ['component_id'], ['component_id'])
    except InternalError as e:
        print(str(e))

    # get existing components
    app_ids = {}
    for component in db.session.query(Component).all():
        app_ids[component.app_id] = component

    # add any extra we need, incrementing the count otherwise
    reviews = db.session.query(Review).all()
    for review in reviews:
        if review._app_id not in app_ids:
            print('adding', review._app_id)
            component = Component(review._app_id)
            db.session.add(component)
            app_ids[component.app_id] = component
        else:
            component = app_ids[review._app_id]
            component.review_cnt += 1
    db.session.commit()

    # fix up the component_id on the existing reviews
    for review in reviews:
        review.component_id = app_ids[review._app_id].component_id
    db.session.commit()

def downgrade():
    #op.drop_constraint(None, 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'component_id')
    op.drop_table('components')
