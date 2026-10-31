import pytest

from app.exceptions import BusinessRuleViolation, NotFound
from app.schemas.customer import CustomerCreate
from tests.helpers import make_customer


def test_rule2_duplicate_email_is_rejected(s):
    make_customer(s, email="a@example.com")
    with pytest.raises(BusinessRuleViolation):
        make_customer(s, email="a@example.com")
    assert len(s.customer.list()) == 1


def test_rule2_email_uniqueness_ignores_case_and_whitespace(s):
    make_customer(s, email="a@example.com")
    with pytest.raises(BusinessRuleViolation):
        s.customer.create(CustomerCreate(name="Other", email="  A@EXAMPLE.com "))


def test_customer_created_active_and_fetchable(s):
    customer = make_customer(s)
    assert customer.status.value == "active"
    assert s.customer.get(customer.id).email == "billing@acme.com"
    with pytest.raises(NotFound):
        s.customer.get(999)
