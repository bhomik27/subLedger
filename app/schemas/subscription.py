from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SubscriptionStatus


class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_date: date | None = None  # defaults to today in SubscriptionService


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    plan_id: int
    status: SubscriptionStatus
    start_date: date
    current_period_start: date
    current_period_end: date
    cancelled_at: datetime | None
