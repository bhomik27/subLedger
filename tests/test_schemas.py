from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import BillingCycle
from app.schemas.customer import CustomerCreate
from app.schemas.payment import PaymentRecordRequest
from app.schemas.plan import PlanCreate, PlanUpdate
from app.services.billing import add_months, resolve_period
from app.exceptions import BusinessRuleViolation


def _plan(price):
    return PlanCreate(name="Pro", billing_cycle=BillingCycle.MONTHLY, price=price, currency="usd")


def test_money_is_quantized_half_up_to_two_places():
    assert _plan("10.005").price == Decimal("10.01")
    assert _plan(10.005).price == Decimal("10.01")
    assert _plan("10").price == Decimal("10.00")


def test_quantization_runs_before_positivity_check():
    with pytest.raises(ValidationError):
        _plan("0.004")  # becomes 0.00, which is not > 0


def test_rule1_schema_rejects_zero_and_negative_price():
    for bad in ("0", "-5", "0.00"):
        with pytest.raises(ValidationError):
            _plan(bad)


def test_money_must_fit_numeric_12_2():
    assert _plan("9999999999.99").price == Decimal("9999999999.99")
    with pytest.raises(ValidationError):
        _plan("10000000000.00")


def test_currency_and_email_are_normalized():
    assert _plan("1").currency == "USD"
    assert CustomerCreate(name="A", email="  Bob@Example.COM ").email == "bob@example.com"
    with pytest.raises(ValidationError):
        PlanCreate(name="x", billing_cycle="monthly", price="1", currency="US")
    with pytest.raises(ValidationError):
        CustomerCreate(name="A", email="not-an-email")


def test_plan_update_rejects_explicit_null_for_required_field():
    with pytest.raises(ValidationError):
        PlanUpdate(name=None)
    assert PlanUpdate(description=None).description is None  # nullable field is fine


def test_payment_amount_must_be_positive_after_quantization():
    with pytest.raises(ValidationError):
        PaymentRecordRequest(invoice_id=1, amount="0.004", currency="USD", status="success")


def test_add_months_clamps_to_end_of_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_resolve_period_defaults_and_validation():
    start, end = resolve_period(date(2026, 1, 15), BillingCycle.QUARTERLY, None, None)
    assert (start, end) == (date(2026, 1, 15), date(2026, 4, 15))
    with pytest.raises(BusinessRuleViolation):
        resolve_period(date(2026, 1, 15), BillingCycle.MONTHLY, date(2026, 3, 1), date(2026, 3, 1))
