"""

Revision ID: 7c3432c40267
Revises: ef03b3a98056
Create Date: 2019-07-05 14:29:46.410656

"""

# revision identifiers, used by Alembic.
revision = '7c3432c40267'
down_revision = 'ef03b3a98056'

from odrs import db
from odrs.models import Component

def upgrade():

    seen = {}
    for component in db.session.query(Component).\
                        order_by(Component.review_cnt.asc()).all():
        if component.app_id not in seen:
            seen[component.app_id] = component
            continue
        component_old = seen[component.app_id]
        print('duplicate', component.app_id, component.review_cnt)
        if component.review_cnt and component_old.review_cnt:
            component_old.review_cnt += component.review_cnt
        elif component.review_cnt:
            component_old.review_cnt = component.review_cnt
        if component.fetch_cnt and component_old.fetch_cnt:
            component_old.fetch_cnt += component.fetch_cnt
        elif component.fetch_cnt:
            component_old.fetch_cnt = component.fetch_cnt
        for review in component.reviews:
            review.component_id = component_old.component_id
        if component.component_id_parent and not component_old.component_id_parent:
            component_old.component_id_parent = component.component_id_parent
        db.session.delete(component)
    db.session.commit()

def downgrade():
    pass
