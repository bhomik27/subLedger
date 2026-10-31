from datetime import date

import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import BillingCycle, PlanStatus, SubscriptionStatus
from app.schemas.plan import PlanUpdate
from app.schemas.subscription import SubscriptionCreate
from tests.helpers import make_customer, make_plan, make_subscription


def test_subscription_is_created_active_with_period_from_plan_cycle(s):
    plan = make_plan(s, cycle=BillingCycle.QUARTERLY)
    customer = make_customer(s)
    sub = make_subscription(s, customer, plan, start_date=date(2026, 1, 15))
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.current_period_start == date(2026, 1, 15)
    assert sub.current_period_end == date(2026, 4, 15)
    assert sub.cancelled_at is None


def test_rule3_cannot_subscribe_to_inactive_plan(s):
    plan = make_plan(s)
    customer = make_customer(s)
    s.plan.update(plan.id, PlanUpdate(status=PlanStatus.INACTIVE))
    with pytest.raises(BusinessRuleViolation):
        make_subscription(s, customer, plan)
    assert s.subscription.list() == []


def test_rule4_no_second_active_subscription_to_same_plan(s):
    plan = make_plan(s)
    customer = make_customer(s)
    make_subscription(s, customer, plan)
    with pytest.raises(BusinessRuleViolation):
        make_subscription(s, customer, plan)
    assert len(s.subscription.list()) == 1


def test_rule4_allows_other_plan_other_customer_and_resubscribe_after_cancel(s):
    plan_a = make_plan(s, name="A")
    plan_b = make_plan(s, name="B")
    cust_1 = make_customer(s, email="one@example.com")
    cust_2 = make_customer(s, email="two@example.com")

    first = make_subscription(s, cust_1, plan_a)
    make_subscription(s, cust_1, plan_b)  # different plan: fine
    make_subscription(s, cust_2, plan_a)  # different customer: fine

    s.subscription.cancel(first.id)
    make_subscription(s, cust_1, plan_a)  # after cancel: fine
    assert len(s.subscription.list()) == 4


def test_cancel_sets_status_and_timestamp_and_cannot_repeat(s):
    sub = make_subscription(s, make_customer(s), make_plan(s))
    cancelled = s.subscription.cancel(sub.id)
    assert cancelled.status == SubscriptionStatus.CANCELLED
    assert cancelled.cancelled_at is not None
    with pytest.raises(BusinessRuleViolation):
        s.subscription.cancel(sub.id)


def test_unknown_customer_or_plan_raises_not_found(s):
    plan = make_plan(s)
    customer = make_customer(s)
    with pytest.raises(NotFound):
        s.subscription.create(SubscriptionCreate(customer_id=999, plan_id=plan.id))
    with pytest.raises(NotFound):
        s.subscription.create(SubscriptionCreate(customer_id=customer.id, plan_id=999))
    with pytest.raises(NotFound):
        s.subscription.cancel(999)
