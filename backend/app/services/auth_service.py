from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


class EmailAlreadyRegisteredError(Exception):
    """Raised when attempting to register with an email that is already in use."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match an existing user."""


class InactiveUserError(Exception):
    """Raised when an inactive user attempts to authenticate."""


def get_user_by_email(db: Session, email: str) -> User | None:
    """Look up a user by email address (case-insensitive)."""
    normalized = email.strip().lower()
    stmt = select(User).where(func.lower(User.email) == normalized)
    return db.scalar(stmt)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Look up a user by primary key."""
    return db.get(User, user_id)


def register_user(db: Session, payload: UserRegisterRequest) -> tuple[User, str]:
    """Register a new standard user account and return the created user and JWT token."""
    if get_user_by_email(db, payload.email) is not None:
        raise EmailAlreadyRegisteredError("An account with this email already exists.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=UserRole.USER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError("An account with this email already exists.") from exc

    db.refresh(user)
    access_token = create_access_token(user_id=user.id, role=user.role)
    return user, access_token


def authenticate_user(db: Session, payload: UserLoginRequest) -> tuple[User, str]:
    """Validate login credentials and return the authenticated user and JWT token."""
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.is_active:
        raise InactiveUserError("This account is inactive.")

    access_token = create_access_token(user_id=user.id, role=user.role)
    return user, access_token
