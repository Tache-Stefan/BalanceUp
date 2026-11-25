from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ArticleStatus, pg_enum

if TYPE_CHECKING:
    from app.models.user import User


class Article(Base):
    """Financial education article."""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name="published",
        ),
        Index("ix_articles_status", "status", "published_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ArticleStatus] = mapped_column(
        pg_enum(ArticleStatus, "article_status"),
        nullable=False,
        server_default=text("'draft'"),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    author: Mapped["User"] = relationship(back_populates="articles")
