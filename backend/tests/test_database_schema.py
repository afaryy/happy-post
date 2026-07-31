from app.db.models import posts_table


def test_posts_table_has_required_columns() -> None:
    columns = posts_table.c

    assert {"id", "message", "created_at"} == set(columns.keys())
    assert columns.id.primary_key
    assert not columns.message.nullable
    assert not columns.created_at.nullable
    assert columns.created_at.type.timezone
