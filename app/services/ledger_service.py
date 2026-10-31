from collections.abc import Sequence

from app.exceptions import NotFound
from app.models.enums import LedgerEntryType, PaymentAttemptStatus
from app.models.invoice import Invoice
from app.models.ledger_entry import LedgerEntry
from app.models.payment_attempt import PaymentAttempt
from app.repositories.customer import CustomerRepository
from app.repositories.ledger import LedgerRepository


class LedgerService:
    """Append-only ledger (rule 9). Never commits: the calling service commits once so
    the ledger entry is atomic with the operation it records."""

    def __init__(
        self, ledger_repo: LedgerRepository, customer_repo: CustomerRepository
    ) -> None:
        self.ledger_repo = ledger_repo
        self.customer_repo = customer_repo

    def record_invoice_created(self, invoice: Invoice) -> LedgerEntry:
        entry = LedgerEntry(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=LedgerEntryType.INVOICE_CREATED,
            amount=invoice.amount_due,
            currency=invoice.currency,
            reference_id=invoice.id,  # invoice id for invoice_created
            description=(
                f"Invoice {invoice.id} created for {invoice.amount_due} {invoice.currency}"
            ),
        )
        return self.ledger_repo.create(entry)

    def record_payment(self, attempt: PaymentAttempt, invoice: Invoice) -> LedgerEntry:
        succeeded = attempt.status == PaymentAttemptStatus.SUCCESS
        entry = LedgerEntry(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=(
                LedgerEntryType.PAYMENT_SUCCESS if succeeded else LedgerEntryType.PAYMENT_FAILURE
            ),
            amount=attempt.amount,
            currency=attempt.currency,
            reference_id=attempt.id,  # payment attempt id for payment events
            description=(
                f"Payment attempt {attempt.id} "
                f"{'succeeded' if succeeded else 'failed'} for invoice {invoice.id}: "
                f"{attempt.amount} {attempt.currency}"
            ),
        )
        return self.ledger_repo.create(entry)

    def get_customer_ledger(self, customer_id: int) -> Sequence[LedgerEntry]:
        if self.customer_repo.get(customer_id) is None:
            raise NotFound(f"customer {customer_id} not found")
        return self.ledger_repo.list_by_customer(customer_id)
