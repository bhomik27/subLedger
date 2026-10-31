"""Dependency wiring. Each request gets one DB session (FastAPI caches get_db per request),
shared by every repository built for that request."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.customer import CustomerRepository
from app.repositories.invoice import InvoiceRepository
from app.repositories.ledger import LedgerRepository
from app.repositories.payment_attempt import PaymentAttemptRepository
from app.repositories.plan import PlanRepository
from app.repositories.subscription import SubscriptionRepository
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService


def _ledger_service(db: Session) -> LedgerService:
    return LedgerService(LedgerRepository(db), CustomerRepository(db))


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    return PlanService(PlanRepository(db))


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(CustomerRepository(db))


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(
        SubscriptionRepository(db), CustomerRepository(db), PlanRepository(db)
    )


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(
        SubscriptionRepository(db),
        PlanRepository(db),
        InvoiceRepository(db),
        _ledger_service(db),
    )


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(
        InvoiceRepository(db), PaymentAttemptRepository(db), _ledger_service(db)
    )


def get_ledger_service(db: Session = Depends(get_db)) -> LedgerService:
    return _ledger_service(db)
