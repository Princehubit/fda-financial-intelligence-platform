
import jwt
import pytest

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.dependencies import get_current_user


settings = get_settings()


@pytest.mark.parametrize(
    "subject",
    [
        None,
        "",
        "abc",
        "-1",
        "0",
        "2147483648",
        "99999999999",
        123,
        [],
    ],
)
def test_invalid_jwt_subject_is_rejected(subject):
    token = jwt.encode(
        {"sub": subject},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException) as error:
        get_current_user(
            credentials=credentials,
            db=object(),
        )

    assert error.value.status_code == 401
