# SubLedger

A simplified SaaS subscription and billing backend: plans, customers, subscriptions, invoices,
payments and an append-only ledger. Built LLD-first; see **[DESIGN.md](DESIGN.md)** for the ERD,
service/repository tables, business-rule ownership, design pattern, and the invoice and payment flows.

Stack: Python 3.10+, FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite, pytest, Docker.

## Architecture

```
routes -> services -> repositories -> models
          schemas (Pydantic) | core/config | db/session
```

- **Routes** parse input, call one service method, return the response.
- **Services** own every business rule and raise `NotFound` (404) or `BusinessRuleViolation` (409).
- **Repositories** do DB access only (add + flush); services commit once per operation.
- Dependencies are injected with FastAPI `Depends` (`app/api/deps.py`).

```
app/
  main.py  exceptions.py
  core/config.py
  db/{base.py, session.py}
  models/  schemas/  repositories/  services/
  api/{deps.py, routes/}
tests/
```

## Setup

### Local

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for Swagger UI. Tables are created on startup.

### Docker

```bash
docker compose up --build
```

The API is served on http://localhost:8000 and the SQLite file is kept in the `subledger_data` volume.

### Tests

```bash
pytest
```

Tests use in-memory SQLite and cover every business rule at the service level plus the HTTP flow.

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `APP_NAME` | `SubLedger` | API title |
| `DATABASE_URL` | `sqlite:///./subledger.db` | SQLAlchemy URL |
| `SQL_ECHO` | `false` | Log SQL statements |

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /plans | Create a subscription plan |
| GET | /plans | List plans |
| PATCH | /plans/{plan_id} | Update / deactivate a plan |
| POST | /customers | Create a customer |
| GET | /customers | List customers |
| GET | /customers/{customer_id} | Fetch customer details |
| POST | /subscriptions | Create a subscription (created as `active`) |
| GET | /subscriptions | List subscriptions |
| PATCH | /subscriptions/{subscription_id}/cancel | Cancel a subscription |
| POST | /invoices/generate | Generate an invoice for a subscription |
| GET | /invoices/{invoice_id} | Fetch invoice details |
| POST | /payments/record | Record a payment attempt (success or failed) |
| GET | /customers/{customer_id}/ledger | Fetch customer ledger history |

Errors: `404` not found, `409` business rule violated, `422` invalid request body.
Money values are serialized as strings (for example `"100.00"`) to avoid float rounding.

### Quick walkthrough

```bash
curl -X POST localhost:8000/plans -H 'Content-Type: application/json' \
  -d '{"name":"Pro","billing_cycle":"monthly","price":"100.00","currency":"USD"}'
curl -X POST localhost:8000/customers -H 'Content-Type: application/json' \
  -d '{"name":"Acme","email":"billing@acme.com"}'
curl -X POST localhost:8000/subscriptions -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"plan_id":1}'
curl -X POST localhost:8000/invoices/generate -H 'Content-Type: application/json' \
  -d '{"subscription_id":1}'
curl -X POST localhost:8000/payments/record -H 'Content-Type: application/json' \
  -d '{"invoice_id":1,"amount":"40.00","currency":"USD","status":"success","provider_reference":"pay_1"}'
curl localhost:8000/customers/1/ledger
```

## Business rules and where they live

| # | Rule | Owner |
|---|---|---|
| 1 | Plan price > 0 | PlanService (+ schema, DB CHECK) |
| 2 | Customer email unique | CustomerService (+ DB UNIQUE) |
| 3 | No subscription on an inactive plan | SubscriptionService |
| 4 | No two active subscriptions to the same plan | SubscriptionService |
| 5 | `amount_due` = plan price at generation time | InvoiceService |
| 6 | Successful payment cannot exceed remaining amount | PaymentService |
| 7 | Fully paid -> `paid`, partial -> `partially_paid` | PaymentService |
| 8 | Failed payment never increases `amount_paid` | PaymentService |
| 9 | Ledger append-only, traceable via `reference_id` | LedgerService + LedgerRepository |

## Assumptions

Everything the brief leaves open is listed in DESIGN.md and marked *(assumed)*. The main ones:

- Plan/customer status: `active` / `inactive`. Subscription status: `active` / `cancelled`.
- Subscriptions are created directly as `active`; there is no separate activate endpoint.
- Invoices are created as `issued`. Billing period defaults to the subscription's current period start plus one billing cycle (monthly 1, quarterly 3, yearly 12 months); `due_date` = `period_end`.
- Payments are accepted only on `issued` or `partially_paid` invoices, with a matching currency and an amount > 0.
- Ledger `reference_id` is the invoice id for `invoice_created` and the payment attempt id for payment events.
- Amounts are rounded half-up to 2 decimal places on input.

## Limitations

- `provider_reference` is not unique, so duplicate submissions are not detected.
- Rule 4 is enforced in the service only; concurrent requests could create duplicates (no DB-level partial unique index).
- SQLite stores decimals as floating point internally; use PostgreSQL for exact decimal storage. SQLite also returns datetimes without timezone info.
- No pagination, no migrations (tables created on startup), no authentication.
- `overdue` / `void` invoice statuses exist but are unreachable; `draft` is unused.
- A failed payment reported against a non-payable invoice (for example `paid`) is rejected and not ledgered.
- No duplicate-invoice-per-period check; custom billing cycles, proration, tax and real gateways are out of scope.
- No endpoint to change customer status or to fetch a single subscription.
