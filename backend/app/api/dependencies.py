from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import InvalidTokenError, decode_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from a Bearer JWT token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Authentication credentials were not provided.")

    try:
        token_payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise _unauthorized(str(exc)) from exc

    try:
        user_id = int(token_payload.sub)
    except ValueError as exc:
        raise _unauthorized("Invalid authentication credentials.") from exc

    user = get_user_by_id(db, user_id)
    if user is None:
        raise _unauthorized("User account not found.")

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Create a FastAPI dependency that restricts access to specific user roles."""

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource.",
            )
        return current_user

    return role_checker


require_role = require_roles
