class DomainError(Exception):
    """Base class for errors raised by services. One handler maps this to HTTP in main.py."""

    def __init__(self, message: str = "") -> None:
        self.message = message or self.__class__.__name__
        super().__init__(self.message)


class NotFound(DomainError):
    """A referenced entity does not exist (mapped to 404)."""


class BusinessRuleViolation(DomainError):
    """A business rule was broken (mapped to 409)."""
