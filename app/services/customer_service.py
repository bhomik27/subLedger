from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError

from app.exceptions import BusinessRuleViolation, NotFound
from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository) -> None:
        self.customer_repo = customer_repo

    def create(self, data: CustomerCreate) -> Customer:
        email = data.email.strip().lower()
        # Rule 2: checked here for a clean error; the DB UNIQUE constraint is the backstop.
        if self.customer_repo.get_by_email(email) is not None:
            raise BusinessRuleViolation(f"email {email} is already registered")
        customer = Customer(name=data.name, email=email, company_name=data.company_name)
        try:
            self.customer_repo.add(customer)
            self.customer_repo.commit()
        except IntegrityError:
            self.customer_repo.rollback()
            raise BusinessRuleViolation(f"email {email} is already registered") from None
        return customer

    def get(self, customer_id: int) -> Customer:
        customer = self.customer_repo.get(customer_id)
        if customer is None:
            raise NotFound(f"customer {customer_id} not found")
        return customer

    def list(self) -> Sequence[Customer]:
        return self.customer_repo.list()
