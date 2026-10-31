from datetime import date
from decimal import Decimal

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.enums import InvoiceStatus, SubscriptionStatus
from app.models.invoice import Invoice
from app.repositories.invoice import InvoiceRepository
from app.repositories.plan import PlanRepository
from app.repositories.subscription import SubscriptionRepository
from app.services.billing import resolve_period
from app.services.ledger_service import LedgerService


class InvoiceService:
    """Generates and fetches invoices. Payment-driven status changes belong to
    PaymentService (DESIGN.md decision D2)."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        ledger_service: LedgerService,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service

    def generate_invoice(
        self,
        subscription_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> Invoice:
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFound(f"subscription {subscription_id} not found")
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise BusinessRuleViolation("cannot invoice a subscription that is not active")

        # D5: the plan's own status is not checked; only the subscription's.
        plan = self.plan_repo.get(subscription.plan_id)
        if plan is None:
            raise NotFound(f"plan {subscription.plan_id} not found")

        start, end = resolve_period(
            subscription.current_period_start, plan.billing_cycle, period_start, period_end
        )
        invoice = self.invoice_repo.add(
            Invoice(
                subscription_id=subscription.id,
                customer_id=subscription.customer_id,
                amount_due=plan.price,  # rule 5: snapshot of the price right now
                amount_paid=Decimal("0.00"),
                currency=plan.currency,
                status=InvoiceStatus.ISSUED,
                period_start=start,
                period_end=end,
                due_date=end,
            )
        )
        self.ledger_service.record_invoice_created(invoice)  # flush only
        self.invoice_repo.commit()  # invoice + ledger entry are atomic
        return invoice

    def get(self, invoice_id: int) -> Invoice:
        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise NotFound(f"invoice {invoice_id} not found")
        return invoice
