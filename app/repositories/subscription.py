from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.enums import SubscriptionStatus
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository):
    def add(self, subscription: Subscription) -> Subscription:
        self.db.add(subscription)
        self.db.flush()
        return subscription

    def get(self, subscription_id: int) -> Subscription | None:
        return self.db.get(Subscription, subscription_id)

    def list(self) -> Sequence[Subscription]:
        return list(self.db.scalars(select(Subscription).order_by(Subscription.id)))

    def find_active(self, customer_id: int, plan_id: int) -> Subscription | None:
        stmt = select(Subscription).where(
            Subscription.customer_id == customer_id,
            Subscription.plan_id == plan_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        return self.db.scalars(stmt).first()

    def save(self, subscription: Subscription) -> Subscription:
        self.db.flush()
        return subscription
