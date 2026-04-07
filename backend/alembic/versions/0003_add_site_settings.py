"""Add site settings table.

Revision ID: 0003_add_site_settings
Revises: 0002_add_user_profile_fields
Create Date: 2026-04-07 00:00:00
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "0003_add_site_settings"
down_revision = "0002_add_user_profile_fields"
branch_labels = None
depends_on = None


def _should_create_table(table_name: str) -> bool:
    if context.is_offline_mode():
        return True
    return not sa.inspect(op.get_bind()).has_table(table_name)


def _should_drop_table(table_name: str) -> bool:
    if context.is_offline_mode():
        return True
    return sa.inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    if not _should_create_table("site_settings"):
        return

    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("site_name", sa.String(length=120), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    if _should_drop_table("site_settings"):
        op.drop_table("site_settings")
