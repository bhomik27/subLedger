from fastapi import APIRouter, Depends

from app.api.deps import get_payment_service
from app.schemas.invoice import InvoiceRead
from app.schemas.payment import PaymentAttemptRead, PaymentRecordRequest, PaymentRecordResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/record", response_model=PaymentRecordResponse, status_code=201)
def record_payment(
    data: PaymentRecordRequest, service: PaymentService = Depends(get_payment_service)
):
    attempt, invoice = service.record_payment(
        invoice_id=data.invoice_id,
        amount=data.amount,
        currency=data.currency,
        status=data.status,
        provider_reference=data.provider_reference,
        failure_reason=data.failure_reason,
    )
    return PaymentRecordResponse(
        payment_attempt=PaymentAttemptRead.model_validate(attempt),
        invoice=InvoiceRead.model_validate(invoice),
    )
