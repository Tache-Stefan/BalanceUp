from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole

MAX_EMAIL_LENGTH = 255
MAX_BCRYPT_PASSWORD_BYTES = 72


class UserRegisterRequest(BaseModel):
    """Payload for creating a new user account."""

    email: EmailStr
    display_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        normalized = str(value).strip().lower()
        if len(normalized) > MAX_EMAIL_LENGTH:
            raise ValueError(f"Email must be at most {MAX_EMAIL_LENGTH} characters.")
        return normalized

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password", mode="after")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError(
                f"Password must be at most {MAX_BCRYPT_PASSWORD_BYTES} bytes when UTF-8 encoded."
            )
        return value


class UserLoginRequest(BaseModel):
    """Payload for authenticating an existing user."""

    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    """Public representation of a user account (never includes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    current_streak_days: int
    last_activity_date: date | None
    created_at: datetime


class AuthResponse(BaseModel):
    """Authentication response containing a JWT bearer token and user details."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Validated payload decoded from a JWT access token."""

    sub: str
    role: UserRole
    exp: int
