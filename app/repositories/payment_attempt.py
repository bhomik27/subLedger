from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.payment_attempt import PaymentAttempt
from app.repositories.base import BaseRepository


class PaymentAttemptRepository(BaseRepository):
    def add(self, attempt: PaymentAttempt) -> PaymentAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def get(self, attempt_id: int) -> PaymentAttempt | None:
        return self.db.get(PaymentAttempt, attempt_id)

    def list_by_invoice(self, invoice_id: int) -> Sequence[PaymentAttempt]:
        stmt = (
            select(PaymentAttempt)
            .where(PaymentAttempt.invoice_id == invoice_id)
            .order_by(PaymentAttempt.id)
        )
        return list(self.db.scalars(stmt))
