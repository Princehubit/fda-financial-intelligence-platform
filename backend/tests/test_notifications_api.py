from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from app.main import app
from app.db.database import Base, get_db
from app.db.models import Notification


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

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


def create_test_notification(client, headers, transaction_id):
    response = client.post(
        "/api/transactions/",
        json={
            "transaction_id": transaction_id,
            "amount": "10.00",
            "transaction_type": "purchase",
            "merchant_category": "groceries",
            "location": "Bhubaneswar",
            "device": "Test-Device",
            "transaction_date": "2026-11-21T10:30:00",
        },
        headers=headers,
    )

    assert response.status_code == 201

    notifications = client.get(
        "/api/notifications/",
        headers=headers,
    )

    assert notifications.status_code == 200
    assert notifications.json()

    return notifications.json()[0]


def test_list_notifications_requires_authentication(client):
    response = client.get("/api/notifications/")
    assert response.status_code == 401


def test_list_notifications_success(client):
    headers = register_and_login(
        client,
        "notification_list@example.com",
        "Notification List User",
    )

    notification = create_test_notification(
        client,
        headers,
        "TXN-NOTIFICATION-LIST-001",
    )

    response = client.get(
        "/api/notifications/",
        headers=headers,
    )

    assert response.status_code == 200
    assert any(
        item["id"] == notification["id"]
        for item in response.json()
    )


def test_unread_count_success(client):
    headers = register_and_login(
        client,
        "notification_count@example.com",
        "Notification Count User",
    )

    create_test_notification(
        client,
        headers,
        "TXN-NOTIFICATION-COUNT-001",
    )

    response = client.get(
        "/api/notifications/unread-count",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["unread_count"] >= 1


def test_mark_notification_as_read(client):
    headers = register_and_login(
        client,
        "notification_read@example.com",
        "Notification Read User",
    )

    notification = create_test_notification(
        client,
        headers,
        "TXN-NOTIFICATION-READ-001",
    )

    response = client.patch(
        f"/api/notifications/{notification['id']}/read",
        headers=headers,
    )

    assert response.status_code == 200

    notifications = client.get(
        "/api/notifications/",
        headers=headers,
    )

    matching = next(
        item for item in notifications.json()
        if item["id"] == notification["id"]
    )

    assert matching["is_read"] is True


def test_mark_all_notifications_as_read(client):
    headers = register_and_login(
        client,
        "notification_all@example.com",
        "Notification All User",
    )

    create_test_notification(
        client,
        headers,
        "TXN-NOTIFICATION-ALL-001",
    )

    create_test_notification(
        client,
        headers,
        "TXN-NOTIFICATION-ALL-002",
    )

    response = client.patch(
        "/api/notifications/read-all",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["updated_count"] >= 2

    unread = client.get(
        "/api/notifications/unread-count",
        headers=headers,
    )

    assert unread.json()["unread_count"] == 0


def test_get_notification_preferences(client):
    headers = register_and_login(
        client,
        "notification_preferences@example.com",
        "Notification Preferences User",
    )

    response = client.get(
        "/api/notifications/preferences",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["in_app_enabled"] is True
    assert data["transaction_alerts"] is True
    assert data["fraud_alerts"] is True


def test_update_notification_preferences(client):
    headers = register_and_login(
        client,
        "notification_update@example.com",
        "Notification Update User",
    )

    response = client.patch(
        "/api/notifications/preferences",
        json={
            "email_enabled": False,
            "in_app_enabled": True,
            "transaction_alerts": False,
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email_enabled"] is False
    assert data["in_app_enabled"] is True
    assert data["transaction_alerts"] is False

    saved = client.get(
        "/api/notifications/preferences",
        headers=headers,
    )

    assert saved.json()["transaction_alerts"] is False


def test_user_cannot_read_another_users_notification(client):
    owner_headers = register_and_login(
        client,
        "notification_owner@example.com",
        "Notification Owner",
    )

    other_headers = register_and_login(
        client,
        "notification_other@example.com",
        "Notification Other",
    )

    notification = create_test_notification(
        client,
        owner_headers,
        "TXN-NOTIFICATION-PRIVATE-001",
    )

    response = client.patch(
        f"/api/notifications/{notification['id']}/read",
        headers=other_headers,
    )

    assert response.status_code == 404

    owner_notifications = client.get(
        "/api/notifications/",
        headers=owner_headers,
    )

    matching = next(
        item for item in owner_notifications.json()
        if item["id"] == notification["id"]
    )

    assert matching["is_read"] is False
