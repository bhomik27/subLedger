from collections.abc import Sequence
from datetime import date

from app.db.base import utcnow
from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import PlanStatus, SubscriptionStatus
from app.models.subscription import Subscription
from app.repositories.customer import CustomerRepository
from app.repositories.plan import PlanRepository
from app.repositories.subscription import SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate
from app.services.billing import add_billing_cycle


class SubscriptionService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo

    def create(self, data: SubscriptionCreate) -> Subscription:
        customer = self.customer_repo.get(data.customer_id)
        if customer is None:
            raise NotFound(f"customer {data.customer_id} not found")
        plan = self.plan_repo.get(data.plan_id)
        if plan is None:
            raise NotFound(f"plan {data.plan_id} not found")

        # Rule 3
        if plan.status != PlanStatus.ACTIVE:
            raise BusinessRuleViolation("cannot subscribe to an inactive plan")
        # Rule 4
        if self.subscription_repo.find_active(customer.id, plan.id) is not None:
            raise BusinessRuleViolation(
                "customer already has an active subscription to this plan"
            )

        start = data.start_date or date.today()
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,  # created directly as active (no activate route)
            start_date=start,
            current_period_start=start,
            current_period_end=add_billing_cycle(start, plan.billing_cycle),
        )
        self.subscription_repo.add(subscription)
        self.subscription_repo.commit()
        return subscription

    def get(self, subscription_id: int) -> Subscription:
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFound(f"subscription {subscription_id} not found")
        return subscription

    def list(self) -> Sequence[Subscription]:
        return self.subscription_repo.list()

    def cancel(self, subscription_id: int) -> Subscription:
        subscription = self.get(subscription_id)
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise BusinessRuleViolation("subscription is already cancelled")
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = utcnow()
        self.subscription_repo.save(subscription)
        self.subscription_repo.commit()
        return subscription
