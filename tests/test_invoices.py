from datetime import date
from decimal import Decimal

import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import InvoiceStatus, PlanStatus
from app.schemas.plan import PlanUpdate
from tests.helpers import make_customer, make_invoice, make_plan, make_subscription


def test_invoice_is_issued_with_default_period_and_due_date(s):
    invoice = make_invoice(s, price="100.00", start_date=date(2026, 1, 15))
    assert invoice.status == InvoiceStatus.ISSUED
    assert invoice.amount_due == Decimal("100.00")
    assert invoice.amount_paid == Decimal("0.00")
    assert invoice.currency == "USD"
    assert invoice.period_start == date(2026, 1, 15)
    assert invoice.period_end == date(2026, 2, 15)
    assert invoice.due_date == invoice.period_end


def test_rule5_amount_due_is_a_snapshot_of_the_plan_price(s):
    plan = make_plan(s, price="100.00")
    sub = make_subscription(s, make_customer(s), plan, start_date=date(2026, 1, 15))
    first = s.invoice.generate_invoice(sub.id)

    s.plan.update(plan.id, PlanUpdate(price="200.00"))
    second = s.invoice.generate_invoice(sub.id)

    s.db.expire_all()  # force a reload from the database
    assert s.invoice.get(first.id).amount_due == Decimal("100.00")  # unchanged
    assert s.invoice.get(second.id).amount_due == Decimal("200.00")  # new price


def test_explicit_period_wins_and_must_be_ordered(s):
    plan = make_plan(s)
    sub = make_subscription(s, make_customer(s), plan, start_date=date(2026, 1, 15))
    invoice = s.invoice.generate_invoice(sub.id, date(2026, 3, 1), date(2026, 3, 31))
    assert (invoice.period_start, invoice.period_end) == (date(2026, 3, 1), date(2026, 3, 31))
    with pytest.raises(BusinessRuleViolation):
        s.invoice.generate_invoice(sub.id, date(2026, 3, 31), date(2026, 3, 1))


def test_cannot_invoice_a_cancelled_subscription(s):
    sub = make_subscription(s, make_customer(s), make_plan(s))
    s.subscription.cancel(sub.id)
    with pytest.raises(BusinessRuleViolation):
        s.invoice.generate_invoice(sub.id)


def test_d5_invoice_allowed_after_plan_is_deactivated(s):
    plan = make_plan(s)
    sub = make_subscription(s, make_customer(s), plan)
    s.plan.update(plan.id, PlanUpdate(status=PlanStatus.INACTIVE))
    invoice = s.invoice.generate_invoice(sub.id)
    assert invoice.amount_due == Decimal("100.00")


def test_unknown_subscription_or_invoice_raises_not_found(s):
    with pytest.raises(NotFound):
        s.invoice.generate_invoice(999)
    with pytest.raises(NotFound):
        s.invoice.get(999)
