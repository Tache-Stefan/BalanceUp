from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.database import NAMING_CONVENTION, Base
from app.models import Base as ModelsBase


def test_alembic_config_and_script_directory() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    script_dir = ScriptDirectory.from_config(alembic_cfg)
    assert Path(script_dir.dir).resolve() == (backend_dir / "alembic").resolve()
    assert script_dir.get_heads() == []


def test_sqlalchemy_base_metadata_wiring() -> None:
    assert ModelsBase is Base
    assert set(NAMING_CONVENTION).issubset(Base.metadata.naming_convention)


def test_alembic_url_percent_escaping() -> None:
    alembic_cfg = Config()
    url_with_encoded_password = "postgresql+psycopg://user:p%40ss@localhost:5433/BalanceUp"
    alembic_cfg.set_main_option("sqlalchemy.url", url_with_encoded_password.replace("%", "%%"))
    assert alembic_cfg.get_main_option("sqlalchemy.url") == url_with_encoded_password
