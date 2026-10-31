from collections.abc import Sequence
from decimal import Decimal

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.plan import Plan
from app.repositories.plan import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    def __init__(self, plan_repo: PlanRepository) -> None:
        self.plan_repo = plan_repo

    @staticmethod
    def _validate_price(price: Decimal) -> None:
        # Rule 1. Also enforced by the Pydantic schema (422) and a DB CHECK.
        if price <= 0:
            raise BusinessRuleViolation("plan price must be greater than 0")

    def create(self, data: PlanCreate) -> Plan:
        self._validate_price(data.price)
        plan = Plan(
            name=data.name,
            description=data.description,
            billing_cycle=data.billing_cycle,
            price=data.price,
            currency=data.currency,
            status=data.status,
        )
        self.plan_repo.add(plan)
        self.plan_repo.commit()
        return plan

    def get(self, plan_id: int) -> Plan:
        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFound(f"plan {plan_id} not found")
        return plan

    def list(self) -> Sequence[Plan]:
        return self.plan_repo.list()

    def update(self, plan_id: int, data: PlanUpdate) -> Plan:
        """Partial update. Deactivation is status=inactive. Price changes affect
        future invoices only (rule 5)."""
        plan = self.get(plan_id)
        changes = data.model_dump(exclude_unset=True)
        if "price" in changes:
            self._validate_price(changes["price"])
        for field, value in changes.items():
            setattr(plan, field, value)
        self.plan_repo.save(plan)
        self.plan_repo.commit()
        return plan
