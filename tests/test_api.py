from decimal import Decimal


def _setup(client, price="100.00"):
    plan = client.post(
        "/plans",
        json={"name": "Pro", "billing_cycle": "monthly", "price": price, "currency": "usd"},
    )
    assert plan.status_code == 201, plan.text
    customer = client.post(
        "/customers", json={"name": "Acme", "email": "Billing@Acme.com", "company_name": "Acme Inc"}
    )
    assert customer.status_code == 201, customer.text
    sub = client.post(
        "/subscriptions",
        json={
            "customer_id": customer.json()["id"],
            "plan_id": plan.json()["id"],
            "start_date": "2026-01-15",
        },
    )
    assert sub.status_code == 201, sub.text
    return plan.json(), customer.json(), sub.json()


def test_full_billing_flow_over_http(client):
    plan, customer, sub = _setup(client)
    assert plan["currency"] == "USD"
    assert Decimal(plan["price"]) == Decimal("100.00")
    assert customer["email"] == "billing@acme.com"
    assert sub["status"] == "active"
    assert sub["current_period_end"] == "2026-02-15"

    inv = client.post("/invoices/generate", json={"subscription_id": sub["id"]})
    assert inv.status_code == 201, inv.text
    invoice = inv.json()
    assert invoice["status"] == "issued"
    assert invoice["period_end"] == "2026-02-15" and invoice["due_date"] == "2026-02-15"

    def record(amount, status, **extra):
        return client.post(
            "/payments/record",
            json={"invoice_id": invoice["id"], "amount": amount, "currency": "USD",
                  "status": status, "provider_reference": "ref", **extra},
        )

    r = record("40.00", "success")
    assert r.status_code == 201, r.text
    assert r.json()["invoice"]["status"] == "partially_paid"
    assert r.json()["payment_attempt"]["status"] == "success"

    assert record("70.00", "success").status_code == 409  # exceeds the 60.00 remaining

    r = record("60.00", "failed", failure_reason="card declined")
    assert r.status_code == 201
    assert r.json()["invoice"]["status"] == "partially_paid"
    assert Decimal(r.json()["invoice"]["amount_paid"]) == Decimal("40.00")
    assert r.json()["payment_attempt"]["failure_reason"] == "card declined"

    r = record("60.00", "success")
    assert r.json()["invoice"]["status"] == "paid"

    fetched = client.get(f"/invoices/{invoice['id']}")
    assert fetched.status_code == 200 and fetched.json()["status"] == "paid"

    ledger = client.get(f"/customers/{customer['id']}/ledger")
    assert ledger.status_code == 200
    assert [e["entry_type"] for e in ledger.json()] == [
        "invoice_created", "payment_success", "payment_failure", "payment_success",
    ]


def test_error_mapping_404_409_422(client):
    assert client.get("/invoices/999").status_code == 404
    assert client.get("/customers/999").status_code == 404
    assert client.get("/customers/999/ledger").status_code == 404
    assert client.post("/subscriptions", json={"customer_id": 1, "plan_id": 1}).status_code == 404

    bad_price = client.post(
        "/plans", json={"name": "Free", "billing_cycle": "monthly", "price": "0", "currency": "USD"}
    )
    assert bad_price.status_code == 422

    _setup(client)
    dup = client.post("/customers", json={"name": "Other", "email": "billing@acme.com"})
    assert dup.status_code == 409


def test_rules_3_and_4_over_http(client):
    plan, customer, sub = _setup(client)
    again = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert again.status_code == 409  # rule 4

    other = client.post(
        "/plans", json={"name": "Old", "billing_cycle": "yearly", "price": "5", "currency": "USD"}
    ).json()
    deact = client.patch(f"/plans/{other['id']}", json={"status": "inactive"})
    assert deact.status_code == 200 and deact.json()["status"] == "inactive"
    blocked = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": other["id"]})
    assert blocked.status_code == 409  # rule 3


def test_cancel_subscription_and_list_endpoints(client):
    plan, customer, sub = _setup(client)
    r = client.patch(f"/subscriptions/{sub['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled" and r.json()["cancelled_at"] is not None
    assert client.patch(f"/subscriptions/{sub['id']}/cancel").status_code == 409

    assert len(client.get("/plans").json()) == 1
    assert len(client.get("/customers").json()) == 1
    assert len(client.get("/subscriptions").json()) == 1
    inv = client.post("/invoices/generate", json={"subscription_id": sub["id"]})
    assert inv.status_code == 409  # cancelled subscription


def test_plan_patch_rejects_null_for_required_field(client):
    plan, _, _ = _setup(client)
    assert client.patch(f"/plans/{plan['id']}", json={"name": None}).status_code == 422
    assert client.patch(f"/plans/{plan['id']}", json={"price": "-1"}).status_code == 422
    assert client.patch("/plans/999", json={"name": "x"}).status_code == 404
