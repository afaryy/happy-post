from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_routes_return_status_and_version() -> None:
    for path in ("/healthz", "/backend/healthz"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert isinstance(response.json()["version"], str)


def test_version_routes_return_the_same_version() -> None:
    assert client.get("/version").json() == client.get("/backend/version").json()
