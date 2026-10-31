from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import BillingCycle
from app.repositories.customer import CustomerRepository
from app.repositories.invoice import InvoiceRepository
from app.repositories.ledger import LedgerRepository
from app.repositories.payment_attempt import PaymentAttemptRepository
from app.repositories.plan import PlanRepository
from app.repositories.subscription import SubscriptionRepository
from app.schemas.customer import CustomerCreate
from app.schemas.plan import PlanCreate
from app.schemas.subscription import SubscriptionCreate
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService


@dataclass
class Services:
    db: Session
    plan: PlanService
    customer: CustomerService
    subscription: SubscriptionService
    invoice: InvoiceService
    payment: PaymentService
    ledger: LedgerService
    invoice_repo: InvoiceRepository
    attempt_repo: PaymentAttemptRepository


def build_services(db: Session) -> Services:
    plan_repo = PlanRepository(db)
    customer_repo = CustomerRepository(db)
    subscription_repo = SubscriptionRepository(db)
    invoice_repo = InvoiceRepository(db)
    attempt_repo = PaymentAttemptRepository(db)
    ledger = LedgerService(LedgerRepository(db), customer_repo)
    return Services(
        db=db,
        plan=PlanService(plan_repo),
        customer=CustomerService(customer_repo),
        subscription=SubscriptionService(subscription_repo, customer_repo, plan_repo),
        invoice=InvoiceService(subscription_repo, plan_repo, invoice_repo, ledger),
        payment=PaymentService(invoice_repo, attempt_repo, ledger),
        ledger=ledger,
        invoice_repo=invoice_repo,
        attempt_repo=attempt_repo,
    )


def make_plan(s, price="100.00", currency="USD", cycle=BillingCycle.MONTHLY, name="Pro"):
    return s.plan.create(
        PlanCreate(name=name, billing_cycle=cycle, price=price, currency=currency)
    )


def make_customer(s, email="billing@acme.com", name="Acme"):
    return s.customer.create(CustomerCreate(name=name, email=email))


def make_subscription(s, customer, plan, start_date=None):
    return s.subscription.create(
        SubscriptionCreate(customer_id=customer.id, plan_id=plan.id, start_date=start_date)
    )


def make_invoice(s, price="100.00", start_date=date(2026, 1, 15)):
    """Plan + customer + subscription + issued invoice. Returns the invoice."""
    plan = make_plan(s, price=price)
    customer = make_customer(s)
    subscription = make_subscription(s, customer, plan, start_date=start_date)
    return s.invoice.generate_invoice(subscription.id)


def pay(s, invoice, amount, status="success", currency="USD", ref="ref", reason=None):
    return s.payment.record_payment(
        invoice.id, Decimal(amount), currency, status, ref, reason
    )
