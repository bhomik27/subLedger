from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentAttemptStatus
from app.schemas.common import CurrencyCode, PositiveMoney
from app.schemas.invoice import InvoiceRead


class PaymentRecordRequest(BaseModel):
    invoice_id: int
    amount: PositiveMoney
    currency: CurrencyCode
    status: PaymentAttemptStatus
    provider_reference: str | None = Field(default=None, max_length=255)
    failure_reason: str | None = None  # only stored when status is "failed"


class PaymentAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    status: PaymentAttemptStatus
    provider_reference: str | None
    failure_reason: str | None
    created_at: datetime


class PaymentRecordResponse(BaseModel):
    payment_attempt: PaymentAttemptRead
    invoice: InvoiceRead  # carries the updated invoice status and amount_paid
