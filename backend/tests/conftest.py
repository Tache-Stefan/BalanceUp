from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.core.database import Base, engine, get_db
from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def ensure_schema() -> None:
    """Ensure all SQLAlchemy tables exist on fresh PostgreSQL instances (e.g., in CI)."""
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session(ensure_schema: None) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session wrapped in a transaction that rolls back after each test."""
    del ensure_schema
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Yield a FastAPI TestClient wired to the isolated transactional test session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.clear()
