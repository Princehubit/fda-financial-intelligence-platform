
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from app.main import app
from app.db.database import Base, get_db


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def register_and_login(client, email, full_name):
    registration = client.post(
        "/api/users/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": "SecurePass123",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "SecurePass123",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def transaction_payload(transaction_id="TXN-TEST-001"):
    return {
        "transaction_id": transaction_id,
        "amount": "2499.99",
        "transaction_type": "purchase",
        "merchant_category": "electronics",
        "location": "Bhubaneswar",
        "device": "Test-Device",
        "transaction_date": "2026-11-21T10:30:00",
    }


def test_create_transaction_success(client):
    headers = register_and_login(
        client,
        "transaction@example.com",
        "Transaction User",
    )

    response = client.post(
        "/api/transactions/",
        json=transaction_payload(),
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["transaction_id"] == "TXN-TEST-001"
    assert data["amount"] == "2499.99"
    assert data["merchant_category"] == "electronics"
    assert data["status"] in ["approved", "pending", "blocked"]
    assert data["risk_score"] is not None
    assert data["risk_level"] is not None


def test_create_transaction_requires_authentication(client):
    response = client.post(
        "/api/transactions/",
        json=transaction_payload(),
    )

    assert response.status_code == 401


def test_duplicate_transaction_is_rejected(client):
    headers = register_and_login(
        client,
        "duplicate_txn@example.com",
        "Duplicate User",
    )

    first_response = client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-DUPLICATE"),
        headers=headers,
    )

    second_response = client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-DUPLICATE"),
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_list_transactions_returns_user_transactions(client):
    headers = register_and_login(
        client,
        "list_txn@example.com",
        "List User",
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-LIST-001"),
        headers=headers,
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-LIST-002"),
        headers=headers,
    )

    response = client.get(
        "/api/transactions/",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    transaction_ids = {
        item["transaction_id"] for item in data
    }

    assert transaction_ids == {
        "TXN-LIST-001",
        "TXN-LIST-002",
    }


def test_list_transactions_requires_authentication(client):
    response = client.get("/api/transactions/")

    assert response.status_code == 401


def test_get_transaction_success(client):
    headers = register_and_login(
        client,
        "get_txn@example.com",
        "Get User",
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-GET-001"),
        headers=headers,
    )

    response = client.get(
        "/api/transactions/TXN-GET-001",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["transaction_id"] == "TXN-GET-001"


def test_user_cannot_access_another_users_transaction(client):
    owner_headers = register_and_login(
        client,
        "owner@example.com",
        "Transaction Owner",
    )

    other_headers = register_and_login(
        client,
        "other@example.com",
        "Other User",
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-PRIVATE-001"),
        headers=owner_headers,
    )

    response = client.get(
        "/api/transactions/TXN-PRIVATE-001",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_delete_transaction_success(client):
    headers = register_and_login(
        client,
        "delete_txn@example.com",
        "Delete User",
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-DELETE-001"),
        headers=headers,
    )

    response = client.delete(
        "/api/transactions/TXN-DELETE-001",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        "/api/transactions/TXN-DELETE-001",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_user_cannot_delete_another_users_transaction(client):
    owner_headers = register_and_login(
        client,
        "delete_owner@example.com",
        "Delete Owner",
    )

    other_headers = register_and_login(
        client,
        "delete_other@example.com",
        "Delete Other",
    )

    client.post(
        "/api/transactions/",
        json=transaction_payload("TXN-PROTECTED-001"),
        headers=owner_headers,
    )

    response = client.delete(
        "/api/transactions/TXN-PROTECTED-001",
        headers=other_headers,
    )

    assert response.status_code == 404

    owner_check = client.get(
        "/api/transactions/TXN-PROTECTED-001",
        headers=owner_headers,
    )

    assert owner_check.status_code == 200
