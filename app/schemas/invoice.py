from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import InvoiceStatus


class InvoiceGenerateRequest(BaseModel):
    subscription_id: int
    period_start: date | None = None
    period_end: date | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: date
    created_at: datetime
