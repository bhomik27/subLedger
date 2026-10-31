from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.models.enums import LedgerEntryType, db_enum


class LedgerEntry(Base):
    """Append-only. Only create and read methods exist on LedgerRepository (rule 9)."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    entry_type: Mapped[LedgerEntryType] = mapped_column(db_enum(LedgerEntryType))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    # Invoice id for invoice_created, payment attempt id for payment events.
    # No foreign key: it points at different tables depending on entry_type.
    reference_id: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="ledger_entries")
    invoice: Mapped["Invoice"] = relationship(back_populates="ledger_entries")
