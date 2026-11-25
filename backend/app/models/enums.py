import enum

from sqlalchemy import Enum as SAEnum


class UserRole(str, enum.Enum):
    """Application user role."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    """Moderator profile verification state."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CategoryType(str, enum.Enum):
    """Transaction category direction."""

    INCOME = "income"
    EXPENSE = "expense"


class GoalStatus(str, enum.Enum):
    """Savings goal lifecycle status."""

    ACTIVE = "active"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"


class ChallengeStatus(str, enum.Enum):
    """User challenge participation status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class BadgeCriteria(str, enum.Enum):
    """Criteria type used to award a badge."""

    POINTS = "points"
    STREAK_DAYS = "streak_days"
    CHALLENGES_COMPLETED = "challenges_completed"


class PointsReason(str, enum.Enum):
    """Reason for a points ledger entry."""

    MONTHLY_BUDGET = "monthly_budget"
    CHALLENGE_COMPLETED = "challenge_completed"
    REVERSAL = "reversal"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class ArticleStatus(str, enum.Enum):
    """Publication status of an educational article."""

    DRAFT = "draft"
    PUBLISHED = "published"


class ConsultationStatus(str, enum.Enum):
    """Consultation request workflow state."""

    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    """Consultation payment status."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Build a PostgreSQL ENUM type using enum string values."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [member.value for member in cls],
    )
