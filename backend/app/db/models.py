import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

metadata = sa.MetaData()

posts_table = sa.Table(
    "posts",
    metadata,
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    sa.Column("message", sa.String(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)
