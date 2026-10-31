from decimal import Decimal

import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import BillingCycle, PlanStatus
from app.schemas.plan import PlanCreate, PlanUpdate
from tests.helpers import make_plan


def test_rule1_service_rejects_non_positive_price_on_create(s):
    # model_construct bypasses the schema so the service-level check is what is tested.
    bad = PlanCreate.model_construct(
        name="Free", description=None, billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("0.00"), currency="USD", status=PlanStatus.ACTIVE,
    )
    with pytest.raises(BusinessRuleViolation):
        s.plan.create(bad)
    assert s.plan.list() == []


def test_rule1_service_rejects_non_positive_price_on_update(s):
    plan = make_plan(s)
    with pytest.raises(BusinessRuleViolation):
        s.plan.update(plan.id, PlanUpdate.model_construct(price=Decimal("-1.00")))
    assert s.plan.get(plan.id).price == Decimal("100.00")


def test_partial_update_and_deactivation(s):
    plan = make_plan(s)
    updated = s.plan.update(plan.id, PlanUpdate(status=PlanStatus.INACTIVE, price="150"))
    assert updated.status == PlanStatus.INACTIVE
    assert updated.price == Decimal("150.00")
    assert updated.name == "Pro"  # untouched


def test_get_missing_plan_raises_not_found(s):
    with pytest.raises(NotFound):
        s.plan.get(999)
