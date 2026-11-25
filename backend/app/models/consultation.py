from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ConsultationStatus, PaymentStatus, pg_enum

if TYPE_CHECKING:
    from app.models.user import ModeratorProfile, User


class ConsultationRequest(Base):
    """User request for a paid financial consultation with a moderator."""

    __tablename__ = "consultation_requests"
    __table_args__ = (
        CheckConstraint("user_id <> moderator_id", name="not_self"),
        Index("ix_consultations_user", "user_id", "status"),
        Index("ix_consultations_moderator", "moderator_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    moderator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("moderator_profiles.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConsultationStatus] = mapped_column(
        pg_enum(ConsultationStatus, "consultation_status"),
        nullable=False,
        server_default=text("'pending'"),
    )
    user_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    moderator_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="consultation_requests",
        foreign_keys=[user_id],
    )
    moderator: Mapped["ModeratorProfile"] = relationship(
        back_populates="consultation_requests",
        foreign_keys=[moderator_id],
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="consultation_request")


class Payment(Base):
    """Payment record linked to a consultation request."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(
            "status NOT IN ('succeeded', 'refunded') OR paid_at IS NOT NULL",
            name="date",
        ),
        Index(
            "ux_payment_success",
            "consultation_request_id",
            unique=True,
            postgresql_where=text("status = 'succeeded'"),
        ),
        Index("ix_payments_consultation", "consultation_request_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    consultation_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("consultation_requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False,
        server_default=text("'EUR'"),
    )
    status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, "payment_status"),
        nullable=False,
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    consultation_request: Mapped["ConsultationRequest"] = relationship(back_populates="payments")
