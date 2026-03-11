"""Initial schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-11 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("admin", "uploader", "user", name="userrole", native_enum=False)
user_status_enum = sa.Enum("active", "banned", "pending", name="userstatus", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("status", user_status_enum, nullable=False),
        sa.Column("tracker_credential", sa.String(length=128), nullable=False),
        sa.Column("rss_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tracker_credential"),
        sa.UniqueConstraint("rss_key"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "torrents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("info_hash", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("torrent_path", sa.String(length=1024), nullable=False),
        sa.Column("cover_image_url", sa.String(length=1024), nullable=True),
        sa.Column("nfo_text", sa.Text(), nullable=True),
        sa.Column("media_info", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_torrents_info_hash", "torrents", ["info_hash"], unique=True)
    op.create_index("ix_torrents_owner_id", "torrents", ["owner_id"], unique=False)
    op.create_index("ix_torrents_category_id", "torrents", ["category_id"], unique=False)

    op.create_table(
        "torrent_files",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("torrent_id", sa.Integer(), sa.ForeignKey("torrents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(length=2048), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
    )
    op.create_index("ix_torrent_files_torrent_id", "torrent_files", ["torrent_id"], unique=False)

    op.create_table(
        "download_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("torrent_id", sa.Integer(), sa.ForeignKey("torrents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_download_logs_torrent_id", "download_logs", ["torrent_id"], unique=False)
    op.create_index("ix_download_logs_user_id", "download_logs", ["user_id"], unique=False)

    op.create_table(
        "tracker_user_stats_cache",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("uploaded_bytes", sa.Integer(), nullable=False),
        sa.Column("downloaded_bytes", sa.Integer(), nullable=False),
        sa.Column("ratio", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
    )

    op.create_table(
        "tracker_torrent_stats_cache",
        sa.Column("torrent_id", sa.Integer(), sa.ForeignKey("torrents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("seeders", sa.Integer(), nullable=False),
        sa.Column("leechers", sa.Integer(), nullable=False),
        sa.Column("snatches", sa.Integer(), nullable=False),
        sa.Column("finished", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tracker_torrent_stats_cache")
    op.drop_table("tracker_user_stats_cache")

    op.drop_index("ix_download_logs_user_id", table_name="download_logs")
    op.drop_index("ix_download_logs_torrent_id", table_name="download_logs")
    op.drop_table("download_logs")

    op.drop_index("ix_torrent_files_torrent_id", table_name="torrent_files")
    op.drop_table("torrent_files")

    op.drop_index("ix_torrents_category_id", table_name="torrents")
    op.drop_index("ix_torrents_owner_id", table_name="torrents")
    op.drop_index("ix_torrents_info_hash", table_name="torrents")
    op.drop_table("torrents")

    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
