"""Shared validated types: money, currency code, email.

Money handling (DESIGN.md 2.1): every incoming amount is quantized to 2 decimal places
with ROUND_HALF_UP *before* any further validation, so 0.004 becomes 0.00 and then fails
the "greater than 0" check. Amounts must fit Numeric(12,2): at most 10 digits before the
decimal point.
"""
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

TWO_PLACES = Decimal("0.01")
MAX_ABS_AMOUNT = Decimal("10000000000")  # 10 integer digits + 2 decimals = 12 digits

_CURRENCY_RE = re.compile(r"[A-Z]{3}")
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _to_money(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError("amount must be a number")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value).strip())
        if not amount.is_finite():
            raise ValueError("amount must be a finite number")
        amount = amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("amount is not a valid number") from None
    if abs(amount) >= MAX_ABS_AMOUNT:
        raise ValueError("amount must have at most 10 digits before the decimal point")
    return amount


def _must_be_positive(value: Decimal) -> Decimal:
    if value <= 0:
        raise ValueError("amount must be greater than 0")
    return value


def _normalize_currency(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("currency must be a string")
    code = value.strip().upper()
    if not _CURRENCY_RE.fullmatch(code):
        raise ValueError("currency must be a 3-letter code such as USD")
    return code


def _normalize_email(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("email must be a string")
    email = value.strip().lower()
    if len(email) > 255 or not _EMAIL_RE.fullmatch(email):
        raise ValueError("invalid email address")
    return email


PositiveMoney = Annotated[
    Decimal, BeforeValidator(_to_money), AfterValidator(_must_be_positive)
]
CurrencyCode = Annotated[str, BeforeValidator(_normalize_currency)]
EmailAddress = Annotated[str, BeforeValidator(_normalize_email)]
