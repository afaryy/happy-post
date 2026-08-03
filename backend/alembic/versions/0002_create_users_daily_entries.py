"""Create users, sessions, and daily entries tables.

Revision ID: 0002_create_users_daily_entries
Revises: 0001_create_posts
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_create_users_daily_entries"
down_revision: str | None = "0001_create_posts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("posts")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="users_email_unique"),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token_hash", name="user_sessions_token_hash_unique"),
    )
    op.create_table(
        "daily_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("encouragement_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("encouragement_score >= 1", name="daily_entries_score_min"),
        sa.CheckConstraint("encouragement_score <= 5", name="daily_entries_score_max"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "entry_date", name="daily_entries_user_date_unique"),
    )
    op.create_table(
        "daily_entry_items",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("entry_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("item_no", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(length=180), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["daily_entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entry_id", "item_no", name="daily_entry_items_entry_item_no_unique"),
    )


def downgrade() -> None:
    op.drop_table("daily_entry_items")
    op.drop_table("daily_entries")
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
