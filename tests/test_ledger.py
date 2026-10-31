from decimal import Decimal

import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import LedgerEntryType
from app.repositories.ledger import LedgerRepository
from app.services.ledger_service import LedgerService
from tests.helpers import make_invoice, pay


def test_rule9_ledger_records_all_three_event_types_with_reference_ids(s):
    invoice = make_invoice(s, price="100.00")
    failed, _ = pay(s, invoice, "30.00", status="failed", reason="declined")
    ok, _ = pay(s, invoice, "40.00", status="success")

    entries = s.ledger.get_customer_ledger(invoice.customer_id)

    assert [e.entry_type for e in entries] == [
        LedgerEntryType.INVOICE_CREATED,
        LedgerEntryType.PAYMENT_FAILURE,
        LedgerEntryType.PAYMENT_SUCCESS,
    ]
    assert [e.reference_id for e in entries] == [invoice.id, failed.id, ok.id]
    assert [e.amount for e in entries] == [
        Decimal("100.00"), Decimal("30.00"), Decimal("40.00"),
    ]
    assert all(e.invoice_id == invoice.id for e in entries)
    assert all(e.customer_id == invoice.customer_id for e in entries)


def test_rejected_payment_writes_no_ledger_entry(s):
    invoice = make_invoice(s, price="100.00")
    with pytest.raises(BusinessRuleViolation):
        pay(s, invoice, "999.00")
    entries = s.ledger.get_customer_ledger(invoice.customer_id)
    assert [e.entry_type for e in entries] == [LedgerEntryType.INVOICE_CREATED]


def test_rule9_ledger_has_no_update_or_delete_surface():
    forbidden = ("update", "delete", "remove", "save", "merge")
    for cls in (LedgerRepository, LedgerService):
        for name in forbidden:
            assert not hasattr(cls, name), f"{cls.__name__} must not expose {name}"


def test_ledger_for_unknown_customer_raises_not_found(s):
    with pytest.raises(NotFound):
        s.ledger.get_customer_ledger(999)
