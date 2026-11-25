from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.database import NAMING_CONVENTION, Base
from app.models import Base as ModelsBase

EXPECTED_TABLES = {
    "users",
    "moderator_profiles",
    "categories",
    "transactions",
    "monthly_budgets",
    "savings_goals",
    "challenges",
    "user_challenges",
    "badges",
    "user_badges",
    "points_ledger",
    "articles",
    "consultation_requests",
    "payments",
}


def test_alembic_config_and_script_directory() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    script_dir = ScriptDirectory.from_config(alembic_cfg)
    assert Path(script_dir.dir).resolve() == (backend_dir / "alembic").resolve()
    assert len(script_dir.get_heads()) == 1


def test_sqlalchemy_base_metadata_wiring() -> None:
    assert ModelsBase is Base
    assert set(NAMING_CONVENTION).issubset(Base.metadata.naming_convention)
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_alembic_url_percent_escaping() -> None:
    alembic_cfg = Config()
    url_with_encoded_password = "postgresql+psycopg://user:p%40ss@localhost:5433/BalanceUp"
    alembic_cfg.set_main_option("sqlalchemy.url", url_with_encoded_password.replace("%", "%%"))
    assert alembic_cfg.get_main_option("sqlalchemy.url") == url_with_encoded_password
