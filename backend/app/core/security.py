from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt import PyJWTError
from pydantic import ValidationError

from app.core.config import settings
from app.models.enums import UserRole
from app.schemas.auth import TokenPayload


class InvalidTokenError(Exception):
    """Raised when a JWT access token is invalid, malformed, or expired."""


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a generated salt."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    user_id: int,
    role: UserRole,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given user and role."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token, returning its typed payload."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload.model_validate(payload)
    except (PyJWTError, ValidationError) as exc:
        raise InvalidTokenError("Invalid or expired access token.") from exc
