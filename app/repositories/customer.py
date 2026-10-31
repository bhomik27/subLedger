from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    def add(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer

    def get(self, customer_id: int) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return self.db.scalars(select(Customer).where(Customer.email == email)).first()

    def list(self) -> Sequence[Customer]:
        return list(self.db.scalars(select(Customer).order_by(Customer.id)))
