from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole


def test_hash_and_verify_password() -> None:
    hashed = hash_password("SecurePass123!")

    assert hashed != "SecurePass123!"
    assert hashed != hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_verify_password_handles_invalid_inputs_safely() -> None:
    hashed = hash_password("SecurePass123!")

    assert verify_password("a" * 80, hashed) is False
    assert verify_password("SecurePass123!", "not-a-valid-bcrypt-hash") is False


def test_create_and_decode_access_token() -> None:
    token = create_access_token(user_id=42, role=UserRole.MODERATOR)
    payload = decode_access_token(token)

    assert payload.sub == "42"
    assert payload.role == UserRole.MODERATOR


def test_decode_access_token_rejects_expired_and_invalid_tokens() -> None:
    expired_token = create_access_token(
        user_id=1,
        role=UserRole.USER,
        expires_delta=timedelta(seconds=-5),
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)

    with pytest.raises(InvalidTokenError):
        decode_access_token("not.a.jwt")
