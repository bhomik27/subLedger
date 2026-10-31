from fastapi import APIRouter, Depends

from app.api.deps import get_subscription_service
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionRead, status_code=201)
def create_subscription(
    data: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.create(data)


@router.get("", response_model=list[SubscriptionRead])
def list_subscriptions(service: SubscriptionService = Depends(get_subscription_service)):
    return service.list()


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionRead)
def cancel_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.cancel(subscription_id)
