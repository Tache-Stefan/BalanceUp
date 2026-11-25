from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, VerificationStatus, pg_enum

if TYPE_CHECKING:
    from app.models.consultation import ConsultationRequest
    from app.models.content import Article
    from app.models.finance import Category, MonthlyBudget, SavingsGoal, Transaction
    from app.models.gamification import Challenge, PointsLedger, UserBadge, UserChallenge


class User(Base):
    """Registered user account."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("current_streak_days >= 0", name="current_streak_days_non_negative"),
        CheckConstraint("email LIKE '%_@_%.__%'", name="email"),
        Index("ux_users_email", func.lower(text("email")), unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"),
        nullable=False,
        server_default=text("'user'"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    current_streak_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    moderator_profile: Mapped["ModeratorProfile | None"] = relationship(
        back_populates="user",
        foreign_keys="ModeratorProfile.user_id",
        uselist=False,
    )
    categories: Mapped[list["Category"]] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
    monthly_budgets: Mapped[list["MonthlyBudget"]] = relationship(back_populates="user")
    savings_goals: Mapped[list["SavingsGoal"]] = relationship(back_populates="user")
    created_challenges: Mapped[list["Challenge"]] = relationship(back_populates="creator")
    user_challenges: Mapped[list["UserChallenge"]] = relationship(back_populates="user")
    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="user")
    points_entries: Mapped[list["PointsLedger"]] = relationship(back_populates="user")
    articles: Mapped[list["Article"]] = relationship(back_populates="author")
    consultation_requests: Mapped[list["ConsultationRequest"]] = relationship(
        back_populates="user",
        foreign_keys="ConsultationRequest.user_id",
    )


class ModeratorProfile(Base):
    """Extended profile and verification metadata for financial moderators."""

    __tablename__ = "moderator_profiles"
    __table_args__ = (
        CheckConstraint("experience_years >= 0", name="experience_years_non_negative"),
        CheckConstraint("consultation_price > 0", name="consultation_price_positive"),
        CheckConstraint(
            "consultation_duration_min > 0",
            name="consultation_duration_positive",
        ),
        CheckConstraint(
            "verification_status <> 'approved' "
            "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="verification",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(150), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    accreditation_details: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        pg_enum(VerificationStatus, "verification_status"),
        nullable=False,
        server_default=text("'pending'"),
    )
    verified_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    consultation_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    consultation_duration_min: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    availability_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user: Mapped["User"] = relationship(
        back_populates="moderator_profile",
        foreign_keys=[user_id],
    )
    verifier: Mapped["User | None"] = relationship(foreign_keys=[verified_by])
    consultation_requests: Mapped[list["ConsultationRequest"]] = relationship(
        back_populates="moderator",
        foreign_keys="ConsultationRequest.moderator_id",
    )
