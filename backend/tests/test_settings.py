from app.settings import Settings


def test_default_settings_do_not_require_database_credentials(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert Settings().database_url is None


def test_settings_read_an_optional_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:password@localhost:5432/happy_post")

    assert Settings().database_url == "postgresql+psycopg://user:password@localhost:5432/happy_post"
