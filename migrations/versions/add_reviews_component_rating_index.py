"""Add index on reviews(component_id, rating) for api/ratings aggregation query.

The GET /1.0/reviews/api/ratings endpoint runs:
  SELECT components.app_id, reviews.rating/20, count(reviews.review_id)
  FROM reviews INNER JOIN components ON reviews.component_id = components.component_id
  GROUP BY components.app_id, reviews.rating/20
This index speeds the join and group-by on large reviews tables.

Revision ID: add_reviews_comp_rating_idx
Revises: 10f0fba3e65f
Create Date: 2026-01-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "add_reviews_comp_rating_idx"
down_revision = "10f0fba3e65f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_reviews_component_id_rating"),
            ["component_id", "rating"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_reviews_component_id_rating"))
