# Wise Payment Dashboard

A small Django dashboard (the "Payment Console") for two sandboxes:

- **Wise sends money out:** quote → recipient → transfer → fund → status changes.
- **Stripe takes money in:** a hosted Stripe Checkout page, paid with test cards (or FPX).

The design follows [docs/02-dashboard-rnd.md](docs/02-dashboard-rnd.md) and the R&D notes in [docs/rnd/](docs/rnd/)
(Stripe: [rnd/014](docs/rnd/014-stripe-sandbox.md)).

## Pages

| Page | What it shows |
|---|---|
| Login | Django username/password login. Every other page needs it |
| Overview | Connection to Wise, your business profile, balances (with sandbox **Top up**), recent transfers |
| Send money | 3 steps: amount → recipient (existing, or new name + IBAN) → review the price and create the transfer |
| Transfers | Every transfer this dashboard created, filterable by Waiting / Processing / Sent / Problem |
| Transfer detail | Fund from balance, Refresh status, sandbox **Simulate → next status**, status history, all IDs, its API calls |
| Recipients | Your EUR recipients, loaded live from Wise |
| Receive money (Stripe) | Amount in MYR + description → you go to Stripe's payment page → back to the dashboard |
| Payments (Stripe) | Every Stripe payment, with its status (Waiting for customer / Paid / Processing / Expired), Refresh, IDs, API calls |
| API log | Every call made to Wise and Stripe: method, path, HTTP status, time, trace ID. Never tokens, keys or bank details |

The Wise route is fixed to **GBP balance → EUR (IBAN)**; Stripe receives **MYR**.

## Setup (once)

You need Python 3.14 and [uv](https://docs.astral.sh/uv/). Run everything from this folder (the one with `pyproject.toml`).

```sh
uv sync                                  # install the packages into .venv
cp .env.example .env                     # then edit .env (see below)
cd wisepaymentdashboard
uv run python manage.py migrate          # create the database tables
uv run python manage.py createsuperuser  # your dashboard login
```

In `.env`, set:

- `WISE_API_TOKEN`: your sandbox **personal API token**. Create it at <https://wise-sandbox.com> under
  *Your Account → Connect and manage apps → API tokens* with **full** access. The sandbox 2FA code is `111111`.
- `STRIPE_SECRET_KEY`: the **secret key of a Stripe sandbox** (starts with `sk_test_`). Sign up at
  <https://dashboard.stripe.com>, open **Sandboxes** in the account picker, create or open a sandbox, then
  **Developers → API keys**. Live keys (`sk_live_`) are refused on purpose.
- `DJANGO_SECRET_KEY`: any long random text. Generate one with
  `uv run python -c "import secrets; print(secrets.token_urlsafe(50))"`.

That's all. The database is SQLite by default; to use PostgreSQL, set `DATABASE_URL` (example in `.env.example`).

## Check that Wise works

```sh
cd wisepaymentdashboard
uv run python manage.py wise_smoke_test
```

This sends one 10 GBP test transfer through the whole flow and prints each step. If a step fails, it tells
you which one and why. The likely problems are already in the R&D notes:

| Step that fails | Probably | What to do |
|---|---|---|
| 1. Business profile (401) | Wrong or missing token | Check `WISE_API_TOKEN` in `.env` |
| 1. Business profile (no BUSINESS) | Only a personal profile exists | Create a business profile (UK, Sole Trader) in the sandbox website |
| 2. Balance (403 `invalid.profile.type`) | The business profile cannot hold balances. Seen on a Malaysian Sole Trader profile (20 Oct 2026): Wise Business in Malaysia has no multi-currency account | Add a **UK, Sole Trader** business profile in the sandbox website, then put its ID in `WISE_PROFILE_ID` in `.env` (the Overview page lists every profile ID) |
| 3. Quote / 4. Recipient (401/403) | The personal token may not call these endpoints (rnd/007, experiment E0) | Write down the error, then ask Wise (`api@wise.com`) |
| 6. Fund (403 or refused) | Country rule or SCA for UK/EEA profiles (rnd/005, experiment E2) | Fund that transfer in the sandbox website, then use the dashboard's **Refresh** and **Simulate** buttons |

## Check that Stripe works

Open the Overview: the Stripe card should say **Connected** and show your sandbox balance. Then
**Receive money** → 10 MYR → on Stripe's page pay with `4242 4242 4242 4242`, expiry `12/34`, any CVC.
You come back to the dashboard and the payment shows **Paid**. The test cards are listed on the page.

## Run the dashboard

```sh
cd wisepaymentdashboard
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000> and log in.

The five-minute demo: **Overview** → **Top up** GBP → **Send money** 100 GBP → **Create transfer** →
**Fund** → **Simulate** three times (wait 5 seconds between clicks) → **Receive money** with a Stripe test card →
look at the **API log**.

## Other commands

```sh
uv run pytest                                       # run the tests (from the folder with pyproject.toml)
uv run python manage.py refresh_statuses            # ask Wise and Stripe about every unfinished transfer/payment
uv run python manage.py loaddata groups             # optional: the "Admin" user group
```

## Where the code lives

```text
wisepaymentdashboard/                  ← BASE_DIR (manage.py)
├── wisepaymentdashboard/settings.py   settings; secrets come from .env
├── templates/                         base layout and login page
├── users/                             custom User model (no extra fields yet)
└── payments/
    ├── providers/wise.py              the ONLY file that calls Wise (token, Decimal parsing, API log, errors)
    ├── providers/stripe.py            the ONLY file that calls Stripe (secret key, version, API log, errors)
    ├── services.py                    the business steps: Wise (quote … simulate), then Stripe (checkout, refresh)
    ├── statuses.py                    provider status → friendly label, colour, final?, next simulation step
    ├── models.py                      Transfer + StatusChange (Wise), Payment (Stripe), ApiCall (API log, both)
    ├── views.py, urls.py, forms.py    the pages (thin: they call services)
    ├── templates/payments/            one template per page
    ├── management/commands/           wise_smoke_test, refresh_statuses
    └── tests/                         fake Wise and Stripe with `responses`; never calls the real APIs
```

How a request flows: **view → service → `WiseClient` / `StripeClient` → provider**, and the service saves the
result in the database.

## Safety rules built in

- Money is `Decimal` everywhere (JSON is parsed with `parse_float=Decimal`), never `float`.
- Each transfer gets a `customerTransactionId` that is saved **before** calling Wise. A retry or double
  click reuses it, so Wise never creates a second transfer.
- Funding counts as done only when Wise's body says `COMPLETED`, never from the HTTP code alone.
- The sandbox panel and top-ups only appear when `WISE_BASE_URL` points at the sandbox.
- Each Stripe payment gets an `Idempotency-Key` saved **before** calling Stripe, for the same reason.
- A Stripe payment counts as paid only when Stripe says `payment_status = paid`.
- Tokens and keys are sent in the `Authorization` header only; they never go into the database, logs or pages.
