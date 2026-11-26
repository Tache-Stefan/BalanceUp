from collections.abc import Generator
from datetime import timedelta

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import require_role, require_roles
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
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
