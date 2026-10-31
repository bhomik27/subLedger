from __future__ import annotations

from app.models.invoice import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository):
    def add(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def get(self, invoice_id: int) -> Invoice | None:
        return self.db.get(Invoice, invoice_id)

    def save(self, invoice: Invoice) -> Invoice:
        self.db.flush()
        return invoice
