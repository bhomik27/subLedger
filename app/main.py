from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models as _models  # noqa: F401  (registers every table on Base.metadata)
from app.api.routes import customers, invoices, ledger, payments, plans, subscriptions
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.exceptions import BusinessRuleViolation, NotFound

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # No migrations in this version: tables are created on startup (see README limitations).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Simplified SaaS subscription and billing backend.",
    lifespan=lifespan,
)


@app.exception_handler(NotFound)
async def not_found_handler(_: Request, exc: NotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(_: Request, exc: BusinessRuleViolation) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


app.include_router(plans.router)
app.include_router(customers.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(ledger.router)
