
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(**overrides):
    values = {
        "database_url": "postgresql+psycopg://test:test@localhost:5432/test",
        "jwt_secret_key": "test-only-secret",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_valid_development_configuration():
    settings = build_settings()

    assert settings.app_env == "development"
    assert settings.debug is True
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


@pytest.mark.parametrize(
    "algorithm",
    ["none", "HS512", "RS256", ""],
)
def test_unsupported_jwt_algorithm_is_rejected(algorithm):
    with pytest.raises(ValidationError):
        build_settings(jwt_algorithm=algorithm)


@pytest.mark.parametrize(
    "expiry",
    [0, -1, 1441, 10000],
)
def test_invalid_token_expiry_is_rejected(expiry):
    with pytest.raises(ValidationError):
        build_settings(access_token_expire_minutes=expiry)


def test_production_debug_mode_is_rejected():
    with pytest.raises(ValidationError):
        build_settings(app_env="production", debug=True)


def test_production_without_debug_is_allowed():
    settings = build_settings(app_env="production", debug=False)

    assert settings.app_env == "production"
    assert settings.debug is False


def test_app_environment_is_normalized():
    settings = build_settings(app_env=" DEVELOPMENT ")

    assert settings.app_env == "development"
