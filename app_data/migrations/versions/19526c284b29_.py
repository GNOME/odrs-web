"""

Revision ID: 19526c284b29
Revises: 84deb10331db
Create Date: 2019-07-02 10:51:23.952062

"""

# revision identifiers, used by Alembic.
revision = '19526c284b29'
down_revision = '84deb10331db'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from odrs import db
from odrs.models import User, Moderator, Event, Review, Vote

def _hash_to_id(user_hash):
    user = db.session.query(User).filter(User.user_hash == user_hash).first()
    if not user:
        return None
    return user.user_id

def upgrade():
    op.add_column('eventlog', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('moderators', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('reviews', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('votes', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'eventlog', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'moderators', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'reviews', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'votes', 'users', ['user_id'], ['user_id'])

    print('CONVERTING Event')
    for val in db.session.query(Event).all():
        val.user_id = _hash_to_id(val.user_hash)
    db.session.commit()

    print('CONVERTING Moderator')
    for val in db.session.query(Moderator).all():
        val.user_id = _hash_to_id(val.user_hash)
    db.session.commit()

    print('CONVERTING Review')
    for val in db.session.query(Review).all():
        val.user_id = _hash_to_id(val.user_hash)
    db.session.commit()

    print('CONVERTING Vote')
    for val in db.session.query(Vote).all():
        val.user_id = _hash_to_id(val.user_hash)
    db.session.commit()

def downgrade():
    op.drop_constraint(None, 'votes', type_='foreignkey')
    op.drop_constraint(None, 'reviews', type_='foreignkey')
    op.drop_constraint(None, 'moderators', type_='foreignkey')
    op.drop_constraint(None, 'eventlog', type_='foreignkey')
    op.drop_column('votes', 'user_id')
    op.drop_column('reviews', 'user_id')
    op.drop_column('moderators', 'user_id')
    op.drop_column('eventlog', 'user_id')
