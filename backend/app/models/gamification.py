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
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BadgeCriteria, ChallengeStatus, PointsReason, pg_enum

if TYPE_CHECKING:
    from app.models.finance import Category
    from app.models.user import User


class Challenge(Base):
    """Spending challenge template created by an admin or moderator."""

    __tablename__ = "challenges"
    __table_args__ = (
        CheckConstraint("max_amount >= 0", name="max_amount_non_negative"),
        CheckConstraint("duration_days > 0", name="duration_days_positive"),
        CheckConstraint("points_reward > 0", name="points_reward_positive"),
        CheckConstraint("available_until >= available_from", name="dates"),
        Index("ix_challenges_available", "available_from", "available_until"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    max_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("0"),
    )
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    available_from: Mapped[date] = mapped_column(Date, nullable=False)
    available_until: Mapped[date] = mapped_column(Date, nullable=False)
    points_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("20"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    creator: Mapped["User"] = relationship(back_populates="created_challenges")
    category: Mapped["Category | None"] = relationship(back_populates="challenges")
    user_challenges: Mapped[list["UserChallenge"]] = relationship(back_populates="challenge")


class UserChallenge(Base):
    """User participation instance for a challenge."""

    __tablename__ = "user_challenges"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="ux_user_challenge"),
        CheckConstraint("ends_at > started_at", name="dates"),
        Index("ix_user_challenges_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    challenge_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenges.id", ondelete="RESTRICT"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ChallengeStatus] = mapped_column(
        pg_enum(ChallengeStatus, "challenge_status"),
        nullable=False,
        server_default=text("'active'"),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="user_challenges")
    challenge: Mapped["Challenge"] = relationship(back_populates="user_challenges")
    points_entries: Mapped[list["PointsLedger"]] = relationship(back_populates="user_challenge")


class Badge(Base):
    """Unlockable gamification badge."""

    __tablename__ = "badges"
    __table_args__ = (CheckConstraint("criteria_value > 0", name="criteria_value_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criteria_type: Mapped[BadgeCriteria] = mapped_column(
        pg_enum(BadgeCriteria, "badge_criteria"),
        nullable=False,
    )
    criteria_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="badge")


class UserBadge(Base):
    """Association table recording badges awarded to users."""

    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    badge_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("badges.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user: Mapped["User"] = relationship(back_populates="user_badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")


class PointsLedger(Base):
    """Immutable ledger of user gamification points."""

    __tablename__ = "points_ledger"
    __table_args__ = (
        CheckConstraint("points_delta <> 0", name="points_delta_non_zero"),
        CheckConstraint(
            "period_month IS NULL OR period_month = DATE_TRUNC('month', period_month)::DATE",
            name="month",
        ),
        CheckConstraint(
            "(reason = 'monthly_budget' AND period_month IS NOT NULL AND points_delta > 0) "
            "OR (reason = 'challenge_completed' AND user_challenge_id IS NOT NULL "
            "AND points_delta > 0) "
            "OR (reason = 'reversal' AND reversal_of_id IS NOT NULL AND points_delta < 0) "
            "OR (reason = 'admin_adjustment')",
            name="reason",
        ),
        Index(
            "ux_points_month",
            "user_id",
            "period_month",
            unique=True,
            postgresql_where=text("reason = 'monthly_budget'"),
        ),
        Index(
            "ux_points_challenge",
            "user_challenge_id",
            unique=True,
            postgresql_where=text("reason = 'challenge_completed'"),
        ),
        Index(
            "ux_points_reversal",
            "reversal_of_id",
            unique=True,
            postgresql_where=text("reason = 'reversal'"),
        ),
        Index("ix_points_user", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[PointsReason] = mapped_column(
        pg_enum(PointsReason, "points_reason"),
        nullable=False,
    )
    period_month: Mapped[date | None] = mapped_column(Date, nullable=True)
    user_challenge_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("user_challenges.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reversal_of_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("points_ledger.id", ondelete="RESTRICT"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user: Mapped["User"] = relationship(back_populates="points_entries")
    user_challenge: Mapped["UserChallenge | None"] = relationship(back_populates="points_entries")
    reversed_entry: Mapped["PointsLedger | None"] = relationship(
        remote_side=[id],
        foreign_keys=[reversal_of_id],
    )
