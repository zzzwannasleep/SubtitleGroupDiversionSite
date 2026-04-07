"""Add audit logs table.

Revision ID: 0004_add_audit_logs
Revises: 0003_add_site_settings
Create Date: 2026-04-07 00:30:00
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "0004_add_audit_logs"
down_revision = "0003_add_site_settings"
branch_labels = None
depends_on = None


def bigint_type() -> sa.TypeEngine[int]:
    return sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def _should_create_table(table_name: str) -> bool:
    if context.is_offline_mode():
        return True
    return not sa.inspect(op.get_bind()).has_table(table_name)


def _should_drop_table(table_name: str) -> bool:
    if context.is_offline_mode():
        return True
    return sa.inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    if not _should_create_table("audit_logs"):
        return

    op.create_table(
        "audit_logs",
        sa.Column("id", bigint_type(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", bigint_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", bigint_type(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"], unique=False)
    op.create_index("ix_audit_logs_target_type", "audit_logs", ["target_type"], unique=False)


def downgrade() -> None:
    if _should_drop_table("audit_logs"):
        op.drop_index("ix_audit_logs_target_type", table_name="audit_logs")
        op.drop_index("ix_audit_logs_target_id", table_name="audit_logs")
        op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
        op.drop_table("audit_logs")
