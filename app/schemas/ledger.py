from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import LedgerEntryType


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    invoice_id: int
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_id: int
    description: str
    created_at: datetime
