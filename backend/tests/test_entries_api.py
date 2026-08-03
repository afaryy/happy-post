from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.routes import current_entry_date
from app.main import create_app
from app.settings import Settings


@pytest.fixture
def client() -> TestClient:
    client = TestClient(create_app())
    client.post(
        "/api/auth/signup",
        json={"email": "dreamer@example.com", "password": "warm-password-123"},
    )
    return client


def valid_payload() -> dict[str, object]:
    return {
        "happy_items": [
            "Warm tea before bed",
            "A funny message from a friend",
            "The sky looked soft tonight",
        ],
        "encouragement_score": 4,
    }


def expected_today() -> date:
    return current_entry_date(Settings())


def test_today_entry_can_be_created_and_read_back(client: TestClient) -> None:
    saved = client.put("/api/entries/today", json=valid_payload())

    assert saved.status_code == 200
    body = saved.json()
    assert body["entry_date"] == expected_today().isoformat()
    assert [item["content"] for item in body["happy_items"]] == [
        "Warm tea before bed",
        "A funny message from a friend",
        "The sky looked soft tonight",
    ]
    assert [item["item_no"] for item in body["happy_items"]] == [1, 2, 3]
    assert body["encouragement_score"] == 4
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]

    assert client.get("/api/entries/today").json() == body


def test_today_entry_update_replaces_the_existing_day(client: TestClient) -> None:
    first = client.put("/api/entries/today", json=valid_payload()).json()
    updated_payload = valid_payload() | {
        "happy_items": ["Fresh sheets", "Moonlight", "A calm walk", "One extra sparkle"],
        "encouragement_score": 5,
    }

    updated = client.put("/api/entries/today", json=updated_payload)

    assert updated.status_code == 200
    body = updated.json()
    assert body["id"] == first["id"]
    assert [item["content"] for item in body["happy_items"]] == [
        "Fresh sheets",
        "Moonlight",
        "A calm walk",
        "One extra sparkle",
    ]
    assert body["encouragement_score"] == 5


def test_month_entries_are_returned_newest_first(client: TestClient) -> None:
    client.put("/api/entries/today", json=valid_payload())

    response = client.get(f"/api/entries?month={expected_today():%Y-%m}")

    assert response.status_code == 200
    entries = response.json()
    assert [entry["entry_date"] for entry in entries] == [expected_today().isoformat()]


def test_entry_can_be_read_by_date(client: TestClient) -> None:
    saved = client.put("/api/entries/today", json=valid_payload()).json()

    response = client.get(f"/api/entries/{expected_today().isoformat()}")

    assert response.status_code == 200
    assert response.json() == saved


def test_unknown_entry_returns_404(client: TestClient) -> None:
    response = client.get("/api/entries/2026-01-02")

    assert response.status_code == 404
    assert response.json() == {"detail": "Entry not found"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("happy_items", ["Warm tea", "Soft socks"]),
        ("happy_items", ["Warm tea", "Soft socks", "   "]),
        ("happy_items", ["Warm tea", "Soft socks", "x" * 181]),
        ("encouragement_score", 0),
        ("encouragement_score", 6),
    ],
)
def test_entry_validation_rejects_invalid_payloads(
    client: TestClient, field: str, value: object
) -> None:
    payload = valid_payload() | {field: value}

    response = client.put("/api/entries/today", json=payload)

    assert response.status_code == 422


def test_entry_validation_rejects_unexpected_fields(client: TestClient) -> None:
    response = client.put(
        "/api/entries/today",
        json=valid_payload() | {"general_journal_text": "this is not a general journal"},
    )

    assert response.status_code == 422


def test_today_uses_the_configured_product_timezone() -> None:
    settings = Settings(app_timezone="Australia/Melbourne")

    assert current_entry_date(settings, datetime(2026, 8, 2, 23, 30, tzinfo=UTC)) == date(
        2026, 8, 3
    )
