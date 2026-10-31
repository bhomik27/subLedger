from decimal import Decimal

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import InvoiceStatus, PaymentAttemptStatus
from app.models.invoice import Invoice
from app.models.payment_attempt import PaymentAttempt
from app.repositories.invoice import InvoiceRepository
from app.repositories.payment_attempt import PaymentAttemptRepository
from app.services.ledger_service import LedgerService

# D3: only these invoice statuses accept payment attempts (successful or failed).
PAYABLE_STATUSES = (InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID)


class PaymentService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        payment_attempt_repo: PaymentAttemptRepository,
        ledger_service: LedgerService,
    ) -> None:
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.ledger_service = ledger_service

    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        currency: str,
        status: PaymentAttemptStatus | str,
        provider_reference: str | None = None,
        failure_reason: str | None = None,
    ) -> tuple[PaymentAttempt, Invoice]:
        try:
            status = PaymentAttemptStatus(status)
        except ValueError:
            raise BusinessRuleViolation("status must be 'success' or 'failed'") from None

        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise NotFound(f"invoice {invoice_id} not found")

        # All validation happens before any write, so a rejected payment leaves no trace.
        if invoice.status not in PAYABLE_STATUSES:  # D3
            raise BusinessRuleViolation(
                f"invoice is {invoice.status.value} and does not accept payments"
            )
        if amount <= 0:  # D4
            raise BusinessRuleViolation("payment amount must be greater than 0")
        if currency.strip().upper() != invoice.currency:  # D4
            raise BusinessRuleViolation("payment currency does not match the invoice currency")
        remaining = invoice.amount_due - invoice.amount_paid
        if status == PaymentAttemptStatus.SUCCESS and amount > remaining:  # rule 6
            raise BusinessRuleViolation(
                f"payment of {amount} exceeds the remaining unpaid amount of {remaining}"
            )

        attempt = self.payment_attempt_repo.add(
            PaymentAttempt(
                invoice_id=invoice.id,
                amount=amount,
                currency=invoice.currency,
                status=status,
                provider_reference=provider_reference,
                failure_reason=(
                    failure_reason if status == PaymentAttemptStatus.FAILED else None
                ),
            )
        )

        if status == PaymentAttemptStatus.SUCCESS:
            invoice.amount_paid = invoice.amount_paid + amount
            # Rule 7
            invoice.status = (
                InvoiceStatus.PAID
                if invoice.amount_paid >= invoice.amount_due
                else InvoiceStatus.PARTIALLY_PAID
            )
            self.invoice_repo.save(invoice)
        # Rule 8: on failure the invoice is not touched at all.

        self.ledger_service.record_payment(attempt, invoice)  # flush only
        self.payment_attempt_repo.commit()  # attempt + invoice update + ledger are atomic
        return attempt, invoice
