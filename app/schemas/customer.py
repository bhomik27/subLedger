from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CustomerStatus
from app.schemas.common import EmailAddress


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailAddress
    company_name: str | None = Field(default=None, max_length=255)


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    company_name: str | None
    status: CustomerStatus
    created_at: datetime
