from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import BillingCycle, PlanStatus
from app.schemas.common import CurrencyCode, PositiveMoney


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    billing_cycle: BillingCycle
    price: PositiveMoney  # rule 1 (schema layer)
    currency: CurrencyCode
    status: PlanStatus = PlanStatus.ACTIVE


class PlanUpdate(BaseModel):
    """Partial update. Only fields present in the request body are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    billing_cycle: BillingCycle | None = None
    price: PositiveMoney | None = None
    currency: CurrencyCode | None = None
    status: PlanStatus | None = None

    @model_validator(mode="after")
    def _no_explicit_null_for_required_fields(self) -> "PlanUpdate":
        for field in ("name", "billing_cycle", "price", "currency", "status"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    billing_cycle: BillingCycle
    price: Decimal
    currency: str
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
