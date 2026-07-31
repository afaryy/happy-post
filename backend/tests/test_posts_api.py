from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_create_then_retrieve_a_post(client: TestClient) -> None:
    created = client.post("/api/posts", json={"message": "Hello"})

    assert created.status_code == 201
    post = created.json()
    assert post["message"] == "Hello"
    assert post["id"]
    assert post["created_at"]
    assert client.get(f"/api/posts/{post['id']}").json() == post


def test_list_posts_returns_newest_first(client: TestClient) -> None:
    client.post("/api/posts", json={"message": "first"})
    client.post("/api/posts", json={"message": "second"})

    response = client.get("/api/posts")

    assert response.status_code == 200
    assert [post["message"] for post in response.json()] == ["second", "first"]


def test_unknown_post_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/posts/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_blank_message_is_rejected(client: TestClient) -> None:
    response = client.post("/api/posts", json={"message": "   "})

    assert response.status_code == 422
