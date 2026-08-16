"""Create the initial private maintenance schema.

Revision ID: 0001
Revises: None
Create Date: 2026-08-15
"""

from alembic import op
from vehicle_maintenance.db import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Vehicle Maintenance Planner migrations are forward-only")
