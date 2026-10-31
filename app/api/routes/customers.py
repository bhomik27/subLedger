from fastapi import APIRouter, Depends

from app.api.deps import get_customer_service
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(
    data: CustomerCreate, service: CustomerService = Depends(get_customer_service)
):
    return service.create(data)


@router.get("", response_model=list[CustomerRead])
def list_customers(service: CustomerService = Depends(get_customer_service)):
    return service.list()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int, service: CustomerService = Depends(get_customer_service)
):
    return service.get(customer_id)
