"""

Revision ID: f32bd8265c3b
Revises: a22c286d8094
Create Date: 2019-07-04 16:35:39.673744

"""

# revision identifiers, used by Alembic.
revision = "f32bd8265c3b"
down_revision = "a22c286d8094"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.add_column(
        "components", sa.Column("component_id_parent", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "components_ibfk_4",
        "components",
        "components",
        ["component_id_parent"],
        ["component_id"],
    )


def downgrade():
    op.drop_constraint("components_ibfk_4", "components", type_="foreignkey")
    op.drop_column("components", "component_id_parent")
