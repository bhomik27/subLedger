from fastapi import APIRouter, Depends

from app.api.deps import get_plan_service
from app.schemas.plan import PlanCreate, PlanRead, PlanUpdate
from app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", response_model=PlanRead, status_code=201)
def create_plan(data: PlanCreate, service: PlanService = Depends(get_plan_service)):
    return service.create(data)


@router.get("", response_model=list[PlanRead])
def list_plans(service: PlanService = Depends(get_plan_service)):
    return service.list()


@router.patch("/{plan_id}", response_model=PlanRead)
def update_plan(
    plan_id: int, data: PlanUpdate, service: PlanService = Depends(get_plan_service)
):
    return service.update(plan_id, data)
