import enum

from sqlalchemy import Enum as SAEnum


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentAttemptStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class LedgerEntryType(str, enum.Enum):
    INVOICE_CREATED = "invoice_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"


def db_enum(enum_cls: type[enum.Enum]) -> SAEnum:
    """Store the enum's *value* (e.g. 'partially_paid') in a plain VARCHAR column."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=20,
        values_callable=lambda e: [member.value for member in e],
        validate_strings=True,
    )
