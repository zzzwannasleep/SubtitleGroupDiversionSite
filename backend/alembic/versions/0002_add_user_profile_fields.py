"""Add avatar and bio fields to users.

Revision ID: 0002_add_user_profile_fields
Revises: 0001_initial_schema
Create Date: 2026-03-11 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_user_profile_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=1024), nullable=True))
        batch_op.add_column(sa.Column("bio", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("bio")
        batch_op.drop_column("avatar_url")
