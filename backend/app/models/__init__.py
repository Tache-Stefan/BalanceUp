from app.core.database import Base

# Import all SQLAlchemy ORM models here so Base.metadata registers every table
# before running `alembic revision --autogenerate`.
__all__ = ["Base"]
