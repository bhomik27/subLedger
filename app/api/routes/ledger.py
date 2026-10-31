from fastapi import APIRouter, Depends

from app.api.deps import get_ledger_service
from app.schemas.ledger import LedgerEntryRead
from app.services.ledger_service import LedgerService

router = APIRouter(tags=["ledger"])


@router.get("/customers/{customer_id}/ledger", response_model=list[LedgerEntryRead])
def get_customer_ledger(
    customer_id: int, service: LedgerService = Depends(get_ledger_service)
):
    return service.get_customer_ledger(customer_id)
