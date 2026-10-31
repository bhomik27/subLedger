from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all models."""


def utcnow() -> datetime:
    """Timezone-aware current time in UTC, used for created_at / updated_at defaults."""
    return datetime.now(timezone.utc)
