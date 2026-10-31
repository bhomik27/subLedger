"""Pure date helpers for billing periods (DESIGN.md decision D1)."""
import calendar
from datetime import date

from app.exceptions import BusinessRuleViolation
from app.models.enums import BillingCycle

CYCLE_MONTHS: dict[BillingCycle, int] = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.YEARLY: 12,
}


def add_months(start: date, months: int) -> date:
    """Add calendar months, clamping the day (31 Jan + 1 month = 28/29 Feb)."""
    index = start.year * 12 + (start.month - 1) + months
    year, month_zero_based = divmod(index, 12)
    month = month_zero_based + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_billing_cycle(start: date, cycle: BillingCycle) -> date:
    return add_months(start, CYCLE_MONTHS[cycle])


def resolve_period(
    default_start: date,
    cycle: BillingCycle,
    period_start: date | None,
    period_end: date | None,
) -> tuple[date, date]:
    """period_start defaults to the subscription's current_period_start; period_end
    defaults to period_start + one billing cycle. Supplied dates win."""
    start = period_start or default_start
    end = period_end or add_billing_cycle(start, cycle)
    if end <= start:
        raise BusinessRuleViolation("period_end must be after period_start")
    return start, end
