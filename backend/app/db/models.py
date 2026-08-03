import sqlalchemy as sa

metadata = sa.MetaData()

users_table = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    sa.Column("email", sa.String(length=320), nullable=False),
    sa.Column("password_hash", sa.String(length=255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("email", name="users_email_unique"),
)

user_sessions_table = sa.Table(
    "user_sessions",
    metadata,
    sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    sa.Column(
        "user_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("session_token_hash", sa.String(length=64), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("session_token_hash", name="user_sessions_token_hash_unique"),
)

daily_entries_table = sa.Table(
    "daily_entries",
    metadata,
    sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    sa.Column(
        "user_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("entry_date", sa.Date(), nullable=False),
    sa.Column("encouragement_score", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("encouragement_score >= 1", name="daily_entries_score_min"),
    sa.CheckConstraint("encouragement_score <= 5", name="daily_entries_score_max"),
    sa.UniqueConstraint("user_id", "entry_date", name="daily_entries_user_date_unique"),
)

daily_entry_items_table = sa.Table(
    "daily_entry_items",
    metadata,
    sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    sa.Column(
        "entry_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("daily_entries.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("item_no", sa.Integer(), nullable=False),
    sa.Column("content", sa.String(length=180), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("entry_id", "item_no", name="daily_entry_items_entry_item_no_unique"),
)
