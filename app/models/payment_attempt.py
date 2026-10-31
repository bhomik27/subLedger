from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.models.enums import PaymentAttemptStatus, db_enum


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentAttemptStatus] = mapped_column(db_enum(PaymentAttemptStatus))
    # Nullable and deliberately NOT unique (listed under limitations in DESIGN.md).
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Set only when status is 'failed'.
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    invoice: Mapped["Invoice"] = relationship(back_populates="payment_attempts")
