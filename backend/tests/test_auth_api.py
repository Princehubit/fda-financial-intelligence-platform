
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db


@pytest.fixture
def client():
    # Create a temporary in-memory SQLite database.
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


def test_user_registration_success(client):
    response = client.post(
        "/api/users/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New Test User",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New Test User"
    assert "password_hash" not in data


def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": "SecurePass123",
    }

    first_response = client.post(
        "/api/users/register",
        json=payload,
    )

    second_response = client.post(
        "/api/users/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_success(client):
    client.post(
        "/api/users/register",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/users/register",
        json={
            "email": "wrongpass@example.com",
            "full_name": "Wrong Password User",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "IncorrectPass123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_authenticated_user_profile(client):
    client.post(
        "/api/users/register",
        json={
            "email": "profile@example.com",
            "full_name": "Profile User",
            "password": "SecurePass123",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "profile@example.com",
            "password": "SecurePass123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/users/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"
    assert response.json()["full_name"] == "Profile User"
    assert "password_hash" not in response.json()
