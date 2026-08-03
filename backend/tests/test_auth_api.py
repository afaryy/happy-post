import sqlalchemy as sa
from fastapi.testclient import TestClient

from app.db.models import metadata
from app.main import create_app
from app.settings import Settings


def test_user_can_sign_up_and_read_their_profile() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/auth/signup",
        json={"email": " Dreamer@Example.COM ", "password": "warm-password-123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "dreamer@example.com"
    assert "password" not in response.text
    assert "password_hash" not in response.text

    profile = client.get("/api/auth/me")
    assert profile.status_code == 200
    assert profile.json()["email"] == "dreamer@example.com"


def test_entries_require_sign_in() -> None:
    client = TestClient(create_app())

    response = client.get("/api/entries/today")

    assert response.status_code == 401


def test_signed_in_users_only_see_their_own_happy_things() -> None:
    first = TestClient(create_app())
    second = TestClient(first.app)

    first.post(
        "/api/auth/signup",
        json={"email": "first@example.com", "password": "warm-password-123"},
    )
    second.post(
        "/api/auth/signup",
        json={"email": "second@example.com", "password": "warm-password-456"},
    )

    save_response = first.put(
        "/api/entries/today",
        json={
            "happy_items": ["Soft rain", "Warm socks", "A tiny moon"],
            "encouragement_score": 5,
        },
    )

    assert save_response.status_code == 200
    assert first.get("/api/entries/today").status_code == 200
    assert second.get("/api/entries/today").status_code == 404


def test_signin_rejects_wrong_password() -> None:
    client = TestClient(create_app())
    client.post(
        "/api/auth/signup",
        json={"email": "dreamer@example.com", "password": "warm-password-123"},
    )
    client.post("/api/auth/signout")

    response = client.post(
        "/api/auth/signin",
        json={"email": "dreamer@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_database_backed_session_works_across_app_instances(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'happy-post.db'}"
    metadata.create_all(sa.create_engine(database_url, future=True))

    first_client = TestClient(create_app(Settings(database_url=database_url)))
    second_client = TestClient(create_app(Settings(database_url=database_url)))

    first_client.post(
        "/api/auth/signup",
        json={"email": "dreamer@example.com", "password": "warm-password-123"},
    )
    session_cookie = first_client.cookies.get("happy_post_session")
    assert session_cookie

    second_client.cookies.set("happy_post_session", session_cookie)

    response = second_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "dreamer@example.com"


def test_signout_invalidates_the_previous_session_token(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'happy-post.db'}"
    metadata.create_all(sa.create_engine(database_url, future=True))
    client = TestClient(create_app(Settings(database_url=database_url)))

    client.post(
        "/api/auth/signup",
        json={"email": "dreamer@example.com", "password": "warm-password-123"},
    )
    old_session_cookie = client.cookies.get("happy_post_session")
    assert old_session_cookie

    assert client.post("/api/auth/signout").status_code == 204
    client.cookies.set("happy_post_session", old_session_cookie)

    response = client.get("/api/auth/me")
    assert response.status_code == 401
