from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.models.enums import BillingCycle, PlanStatus, db_enum


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        # Rule 1 backstop. PlanService and the Pydantic schema are the owners.
        CheckConstraint("price > 0", name="ck_plans_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_cycle: Mapped[BillingCycle] = mapped_column(db_enum(BillingCycle))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PlanStatus] = mapped_column(
        db_enum(PlanStatus), default=PlanStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
