
import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


def test_valid_registration_data():
    user = UserCreate(
        email="test@example.com",
        full_name="Prince Khosala",
        password="SecurePass123",
    )

    assert user.email == "test@example.com"
    assert user.full_name == "Prince Khosala"


def test_registration_trims_full_name():
    user = UserCreate(
        email="test@example.com",
        full_name="  Prince Khosala  ",
        password="SecurePass123",
    )

    assert user.full_name == "Prince Khosala"


@pytest.mark.parametrize(
    "name",
    ["", " ", "   ", "A"],
)
def test_invalid_registration_name_is_rejected(name):
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            full_name=name,
            password="SecurePass123",
        )


def test_registration_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            full_name="Test User",
            password="SecurePass123",
        )


@pytest.mark.parametrize(
    "password",
    ["short", "1234567", "x" * 129],
)
def test_registration_rejects_invalid_password(password):
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            full_name="Test User",
            password=password,
        )


def test_registration_preserves_password_exactly():
    password = "  SecurePass123  "

    user = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password=password,
    )

    assert user.password == password


def test_valid_login_data():
    login = LoginRequest(
        email="test@example.com",
        password="existing-password",
    )

    assert login.email == "test@example.com"


def test_login_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(
            email="test@example.com",
            password="",
        )


def test_login_rejects_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(
            email="invalid-email",
            password="existing-password",
        )


def test_login_preserves_password_exactly():
    password = "  existing-password  "

    login = LoginRequest(
        email="test@example.com",
        password=password,
    )

    assert login.password == password
