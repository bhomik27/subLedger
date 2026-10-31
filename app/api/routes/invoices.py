from fastapi import APIRouter, Depends

from app.api.deps import get_invoice_service
from app.schemas.invoice import InvoiceGenerateRequest, InvoiceRead
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/generate", response_model=InvoiceRead, status_code=201)
def generate_invoice(
    data: InvoiceGenerateRequest, service: InvoiceService = Depends(get_invoice_service)
):
    return service.generate_invoice(data.subscription_id, data.period_start, data.period_end)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, service: InvoiceService = Depends(get_invoice_service)):
    return service.get(invoice_id)
