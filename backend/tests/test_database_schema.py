from app.db.models import (
    daily_entries_table,
    daily_entry_items_table,
    user_sessions_table,
    users_table,
)


def test_users_table_has_required_columns() -> None:
    columns = users_table.c

    assert set(columns.keys()) == {"id", "email", "password_hash", "created_at", "updated_at"}
    assert columns.id.primary_key
    assert not columns.email.nullable
    assert not columns.password_hash.nullable
    assert not columns.created_at.nullable
    assert not columns.updated_at.nullable
    assert columns.created_at.type.timezone
    assert columns.updated_at.type.timezone


def test_user_sessions_table_has_required_columns() -> None:
    columns = user_sessions_table.c

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "session_token_hash",
        "expires_at",
        "created_at",
    }
    assert columns.id.primary_key
    assert not columns.user_id.nullable
    assert not columns.session_token_hash.nullable
    assert not columns.expires_at.nullable
    assert not columns.created_at.nullable
    assert columns.expires_at.type.timezone
    assert columns.created_at.type.timezone


def test_daily_entries_table_has_required_columns() -> None:
    columns = daily_entries_table.c

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "entry_date",
        "encouragement_score",
        "created_at",
        "updated_at",
    }
    assert columns.id.primary_key
    assert not columns.user_id.nullable
    assert not columns.entry_date.nullable
    assert not columns.encouragement_score.nullable
    assert not columns.created_at.nullable
    assert not columns.updated_at.nullable
    assert columns.created_at.type.timezone
    assert columns.updated_at.type.timezone


def test_daily_entry_items_table_has_required_columns() -> None:
    columns = daily_entry_items_table.c

    assert set(columns.keys()) == {"id", "entry_id", "item_no", "content", "created_at"}
    assert columns.id.primary_key
    assert not columns.entry_id.nullable
    assert not columns.item_no.nullable
    assert not columns.content.nullable
    assert not columns.created_at.nullable
    assert columns.created_at.type.timezone
