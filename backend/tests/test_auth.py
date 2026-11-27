from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import require_role, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User


def _create_user(
    db: Session,
    *,
    email: str,
    display_name: str = "Test User",
    password: str = "password123",
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_register_creates_user_and_returns_jwt(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": " Maria@Example.COM ",
            "display_name": "  Maria  ",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0

    user = data["user"]
    assert user["email"] == "maria@example.com"
    assert user["display_name"] == "Maria"
    assert user["role"] == "user"
    assert user["is_active"] is True
    assert user["current_streak_days"] == 0
    assert user["last_activity_date"] is None
    assert "created_at" in user
    assert "password_hash" not in user


def test_register_rejects_duplicate_email_case_insensitively(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "display_name": "First User",
        "password": "password123",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json={
            "email": "DUPLICATE@Example.com",
            "display_name": "Second User",
            "password": "password456",
        },
    )
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


def test_register_validates_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "display_name": "A", "password": "short"},
    )
    assert response.status_code == 422


def test_login_succeeds_and_returns_token_and_user(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, email="login@example.com", display_name="Login User")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "LOGIN@Example.com", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["display_name"] == "Login User"
    assert "password_hash" not in data["user"]


def test_login_rejects_wrong_password_and_unknown_email(
    client: TestClient, db_session: Session
) -> None:
    _create_user(db_session, email="known@example.com")

    wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "known@example.com", "password": "wrongpassword"},
    )
    assert wrong_pw.status_code == 401

    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "password123"},
    )
    assert unknown.status_code == 401


def test_login_rejects_inactive_user(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, email="inactive@example.com", is_active=False)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 403


def test_me_returns_authenticated_user(client: TestClient) -> None:
    register_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "display_name": "Current User",
            "password": "password123",
        },
    )
    token = register_res.json()["access_token"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@example.com"
    assert me_res.json()["display_name"] == "Current User"


def test_me_rejects_missing_invalid_expired_and_inactive_tokens(
    client: TestClient, db_session: Session
) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401

    invalid_res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert invalid_res.status_code == 401

    user = _create_user(db_session, email="expired@example.com")
    expired_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(seconds=-10),
    )
    expired_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired_res.status_code == 401

    inactive_user = _create_user(db_session, email="disabled@example.com", is_active=False)
    inactive_token = create_access_token(user_id=inactive_user.id, role=inactive_user.role)
    inactive_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {inactive_token}"},
    )
    assert inactive_res.status_code == 403


def test_rbac_require_roles_enforces_permissions(db_session: Session) -> None:
    rbac_app = FastAPI()

    @rbac_app.get("/admin-only")
    def admin_only(current_user: User = Depends(require_role(UserRole.ADMIN))) -> dict[str, str]:
        return {"role": current_user.role.value}

    @rbac_app.get("/staff-only")
    def staff_only(
        current_user: User = Depends(require_roles(UserRole.MODERATOR, UserRole.ADMIN)),
    ) -> dict[str, str]:
        return {"role": current_user.role.value}

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    rbac_app.dependency_overrides[get_db] = override_get_db

    standard_user = _create_user(db_session, email="std@example.com", role=UserRole.USER)
    moderator_user = _create_user(db_session, email="mod@example.com", role=UserRole.MODERATOR)
    admin_user = _create_user(db_session, email="adm@example.com", role=UserRole.ADMIN)

    user_headers = {
        "Authorization": f"Bearer {create_access_token(standard_user.id, standard_user.role)}"
    }
    mod_headers = {
        "Authorization": f"Bearer {create_access_token(moderator_user.id, moderator_user.role)}"
    }
    admin_headers = {
        "Authorization": f"Bearer {create_access_token(admin_user.id, admin_user.role)}"
    }

    with TestClient(rbac_app) as rbac_client:
        assert rbac_client.get("/admin-only", headers=user_headers).status_code == 403
        assert rbac_client.get("/staff-only", headers=user_headers).status_code == 403

        assert rbac_client.get("/admin-only", headers=mod_headers).status_code == 403
        assert rbac_client.get("/staff-only", headers=mod_headers).status_code == 200

        assert rbac_client.get("/admin-only", headers=admin_headers).status_code == 200
        assert rbac_client.get("/staff-only", headers=admin_headers).status_code == 200


def test_register_hashes_password_and_authenticates_full_lifecycle(
    client: TestClient, db_session: Session
) -> None:
    raw_password = "StrongPassword123!"
    register_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "lifecycle@example.com",
            "display_name": "Lifecycle User",
            "password": raw_password,
        },
    )
    assert register_res.status_code == 201
    register_data = register_res.json()
    user_id = register_data["user"]["id"]

    reg_token_payload = decode_access_token(register_data["access_token"])
    assert reg_token_payload.sub == str(user_id)
    assert reg_token_payload.role == UserRole.USER

    db_user = db_session.get(User, user_id)
    assert db_user is not None
    assert db_user.password_hash != raw_password
    assert db_user.password_hash.startswith("$2")
    assert verify_password(raw_password, db_user.password_hash) is True

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "LIFECYCLE@Example.com", "password": raw_password},
    )
    assert login_res.status_code == 200
    login_token = login_res.json()["access_token"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id
    assert me_res.json()["email"] == "lifecycle@example.com"


def test_register_ignores_privileged_fields_and_defaults_to_active_user(
    client: TestClient, db_session: Session
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "escalation@example.com",
            "display_name": "Normal User",
            "password": "password123",
            "role": "admin",
            "is_active": False,
            "current_streak_days": 99,
        },
    )
    assert response.status_code == 201
    user_data = response.json()["user"]
    assert user_data["role"] == "user"
    assert user_data["is_active"] is True
    assert user_data["current_streak_days"] == 0

    db_user = db_session.get(User, user_data["id"])
    assert db_user is not None
    assert db_user.role == UserRole.USER
    assert db_user.is_active is True


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "bytes@example.com", "display_name": "Byte Limit", "password": "a" * 73},
        {"email": "utf8@example.com", "display_name": "UTF8 Limit", "password": "ă" * 37},
        {"email": "blank@example.com", "display_name": "   ", "password": "password123"},
    ],
)
def test_register_rejects_overlong_password_and_blank_display_name(
    client: TestClient, payload: dict[str, str]
) -> None:
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": "password123"},
        {"email": "user@example.com", "password": ""},
    ],
)
def test_login_validates_payload(client: TestClient, payload: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 422


def test_login_unauthorized_includes_bearer_challenge(
    client: TestClient, db_session: Session
) -> None:
    _create_user(db_session, email="challenge@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "challenge@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_me_rejects_wrong_scheme_wrong_secret_bad_claims_and_unknown_user(
    client: TestClient, db_session: Session
) -> None:
    user = _create_user(db_session, email="token-checks@example.com")
    now = datetime.now(UTC)
    exp = int((now + timedelta(minutes=15)).timestamp())

    wrong_secret_token = jwt.encode(
        {"sub": str(user.id), "role": user.role.value, "exp": exp},
        "completely-wrong-secret-key",
        algorithm=settings.JWT_ALGORITHM,
    )
    missing_role_token = jwt.encode(
        {"sub": str(user.id), "exp": exp},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    non_int_sub_token = jwt.encode(
        {"sub": "not-an-int", "role": user.role.value, "exp": exp},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    unknown_user_token = create_access_token(user_id=999_999_999, role=UserRole.USER)

    invalid_headers = [
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer "},
        {"Authorization": f"Bearer {wrong_secret_token}"},
        {"Authorization": f"Bearer {missing_role_token}"},
        {"Authorization": f"Bearer {non_int_sub_token}"},
        {"Authorization": f"Bearer {unknown_user_token}"},
    ]

    for headers in invalid_headers:
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        assert response.headers.get("www-authenticate") == "Bearer"
