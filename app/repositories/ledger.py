from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.ledger_entry import LedgerEntry
from app.repositories.base import BaseRepository


class LedgerRepository(BaseRepository):
    """Append-only (rule 9): create and read methods only. No update, save or delete."""

    def create(self, entry: LedgerEntry) -> LedgerEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_by_customer(self, customer_id: int) -> Sequence[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.customer_id == customer_id)
            .order_by(LedgerEntry.created_at, LedgerEntry.id)
        )
        return list(self.db.scalars(stmt))
