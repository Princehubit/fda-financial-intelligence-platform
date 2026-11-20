from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "FDA Financial Intelligence Platform"


def test_core_api_routes_are_registered():
    paths = app.openapi()["paths"]

    expected_routes = {
        "/api/users/register",
        "/api/users/me",
        "/api/auth/login",
        "/api/transactions/",
        "/api/transactions/{transaction_id}",
    }

    assert expected_routes.issubset(paths.keys())
