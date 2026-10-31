from decimal import Decimal

import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import InvoiceStatus, PaymentAttemptStatus
from tests.helpers import make_invoice, pay


def _reload(s, invoice):
    s.db.expire_all()
    return s.invoice_repo.get(invoice.id)


def test_rule6_successful_payment_cannot_exceed_remaining_amount(s):
    invoice = make_invoice(s, price="100.00")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "100.01")

    pay(s, invoice, "40.00")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "60.01")  # only 60.00 remains

    reloaded = _reload(s, invoice)
    assert reloaded.amount_paid == Decimal("40.00")
    assert len(s.attempt_repo.list_by_invoice(invoice.id)) == 1  # rejected ones left no trace


def test_rule7_partial_then_full_payment_moves_status(s):
    invoice = make_invoice(s, price="100.00")

    attempt, inv = pay(s, invoice, "40.00")
    assert attempt.status == PaymentAttemptStatus.SUCCESS
    assert inv.status == InvoiceStatus.PARTIALLY_PAID
    assert inv.amount_paid == Decimal("40.00")

    _, inv = pay(s, invoice, "60.00")
    assert inv.status == InvoiceStatus.PAID
    assert inv.amount_paid == Decimal("100.00")


def test_rule7_single_full_payment_goes_straight_to_paid(s):
    invoice = make_invoice(s, price="100.00")
    _, inv = pay(s, invoice, "100.00")
    assert inv.status == InvoiceStatus.PAID


def test_rule8_failed_payment_does_not_increase_amount_paid(s):
    invoice = make_invoice(s, price="100.00")
    attempt, inv = pay(s, invoice, "30.00", status="failed", reason="card declined")

    assert attempt.status == PaymentAttemptStatus.FAILED
    assert attempt.failure_reason == "card declined"
    reloaded = _reload(s, invoice)
    assert reloaded.amount_paid == Decimal("0.00")
    assert reloaded.status == InvoiceStatus.ISSUED


def test_d4_failed_attempt_is_not_bounded_by_remaining_amount(s):
    invoice = make_invoice(s, price="100.00")
    attempt, _ = pay(s, invoice, "500.00", status="failed", reason="limit")
    assert attempt.amount == Decimal("500.00")
    assert _reload(s, invoice).amount_paid == Decimal("0.00")


def test_failure_reason_is_only_stored_for_failed_attempts(s):
    invoice = make_invoice(s)
    attempt, _ = pay(s, invoice, "10.00", status="success", reason="ignored")
    assert attempt.failure_reason is None


def test_d3_paid_invoice_rejects_further_payments_of_any_kind(s):
    invoice = make_invoice(s, price="100.00")
    pay(s, invoice, "100.00")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "1.00")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "1.00", status="failed")
    assert len(s.attempt_repo.list_by_invoice(invoice.id)) == 1


def test_d4_currency_mismatch_and_non_positive_amount_are_rejected(s):
    invoice = make_invoice(s)
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "10.00", currency="EUR")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "0.00")


def test_invalid_status_and_missing_invoice(s):
    invoice = make_invoice(s)
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "10.00", status="refunded")
    with pytest.raises(NotFound):
        s.payment.record_payment(999, Decimal("1.00"), "USD", "success")
