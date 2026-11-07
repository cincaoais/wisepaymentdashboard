# 014 – Stripe sandbox: receive a payment with Checkout
Date: 20 October 2026
Roadmap step: Phase 7 (Stripe)

## Question
- What is a Stripe sandbox, and which keys does the app use? How are they sent ("API login")?
- What is the smallest real flow for **receiving** money that a server-rendered Django app can show end to end?
- How do we stop a double click or retry from creating two payments (Wise used `customerTransactionId`)?
- How do we know a payment succeeded: redirect, polling or webhooks?
- What does an error look like? Which ID do we log for Stripe support?
- Amounts: decimals or minor units? Which currency for a Malaysian user?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Sandboxes | https://docs.stripe.com/sandboxes | docs.stripe.com | official doc | accessed 2026-10-20 | A sandbox is "an isolated test environment"; payments "aren't processed by card networks"; use general sandboxes for new integrations |
| S2 | API keys | https://docs.stripe.com/keys | docs.stripe.com | official doc | accessed 2026-10-20 | Sandbox keys start `sk_test_` / `rk_test_` / `pk_test_`; "In sandbox mode, you can always see all of your API keys"; never commit keys |
| S3 | Authentication | https://docs.stripe.com/api/authentication | docs.stripe.com | official doc | accessed 2026-10-20 | Basic auth with the key as username, or `Authorization: Bearer`; HTTPS only |
| S4 | Create a Checkout Session | https://docs.stripe.com/api/checkout/sessions/create | docs.stripe.com | official doc | accessed 2026-10-20 | `POST /v1/checkout/sessions`, form-encoded `line_items[0][price_data][…]`, `mode=payment`, `success_url`, `cancel_url`, `client_reference_id`, `expires_at` 30 min–24 h (default 24 h); response has `id` (`cs_test_…`) and `url` |
| S5 | The Checkout Session object | https://docs.stripe.com/api/checkout/sessions/object | docs.stripe.com | official doc | accessed 2026-10-20 | `status` = `open` / `complete` / `expired`; `payment_status` = `paid` / `unpaid` / `no_payment_required`; "complete … Payment processing may still be in progress"; `url` only while active |
| S6 | Idempotent requests | https://docs.stripe.com/api/idempotent_requests | docs.stripe.com | official doc | accessed 2026-10-20 | `Idempotency-Key` header on POST, V4 UUID suggested, ≤255 chars, kept ≥24 h, same key + different params = error, results saved including `500` |
| S7 | Errors | https://docs.stripe.com/api/errors | docs.stripe.com | official doc | accessed 2026-10-20 | One shape: `{"error": {"type", "code", "decline_code", "message", "param", …}}`; codes 400/401/402/403/404/409/424/429/5xx |
| S8 | Versioning | https://docs.stripe.com/api/versioning | docs.stripe.com | official doc | accessed 2026-10-20 | "The current version is 2026-09-30.endive"; pin with the `Stripe-Version` header, else the account default is used |
| S9 | Testing | https://docs.stripe.com/testing | docs.stripe.com | official doc | accessed 2026-10-20 | `4242 4242 4242 4242` succeeds; Malaysia card `4000 0045 8000 0002`; decline `4000 0000 0000 0002`; insufficient funds `4000 0000 0000 9995`; 3DS `4000 0000 0000 3220`; expiry e.g. 12/34, any CVC |
| S10 | Supported currencies | https://docs.stripe.com/currencies | docs.stripe.com | official doc | accessed 2026-10-20 | Amounts in the **minor unit** ("1000 to charge 10 USD"); minimum 2.00 MYR, 0.30 GBP, 0.50 USD |
| S11 | Fulfill orders (hosted page) | https://docs.stripe.com/checkout/fulfillment?payment-ui=stripe-hosted | docs.stripe.com | official doc | accessed 2026-10-20 | Retrieve the session on the landing page and check `payment_status`; fulfil "only once"; "Webhooks are required for fulfillment" in production because customers may never reach the landing page |
| S12 | FPX payments | https://docs.stripe.com/payments/fpx | docs.stripe.com | official doc | accessed 2026-10-20 | Malaysian bank payment; MYR only; MY Stripe accounts only; works with Checkout; enable it in the Dashboard, no code |

## Experiment (request, response, screenshots – key removed)
Status: **Not run yet — needs your sandbox secret key.**
1. Create a Stripe account, open **Sandboxes** in the account picker, create a sandbox, copy its **secret key** (`sk_test_…`) into `.env` as `STRIPE_SECRET_KEY`.
2. Overview page: does the Stripe card show "Connected" and your sandbox balance (`GET /v1/balance`)?
3. **Receive money** → 10.00 MYR → you land on `checkout.stripe.com`. Pay with `4242 4242 4242 4242`, 12/34, any CVC. Back in the dashboard: is it "Paid"?
4. Repeat with the decline card `4000 0000 0000 0002`. What does Checkout show? What is the session status afterwards?
5. Start a payment and press **back** on the Checkout page (cancel). What status does the dashboard show?
6. Optional: enable FPX in the Dashboard (Settings → Payment methods) and pay with FPX. Is the session `complete` + `paid` right away?

## Finding (in your own words)
- **Wise is money out; Stripe is money in.** The Stripe object that matches our "one payment" is a **Checkout Session**: Stripe hosts the payment page, so the dashboard never touches card numbers [S4].
- **"API login" = the secret key.** Stripe has no login call: every request carries the key, as `Authorization: Bearer sk_test_…` [S3]. A sandbox key only sees that sandbox's fake data [S1][S2]. Live keys start `sk_live_` / `rk_live_` [S2].
- **Duplicate protection** works like Wise, but in a header: `Idempotency-Key` on every POST. Same key + same body = Stripe returns the first answer, for at least 24 hours [S6]. So we save a UUID in our row **before** calling Stripe and reuse it on retry (same rule as rnd/004).
- **Two status fields, not one** [S5]:

| `status` | `payment_status` | Our label |
|---|---|---|
| `open` | `unpaid` | Waiting for customer |
| `complete` | `paid` | Paid |
| `complete` | `unpaid` | Processing (some methods confirm later) |
| `expired` | any | Expired |

- **How we know it's paid:** Stripe sends the customer back to our `success_url`; we then **retrieve the session** and read `payment_status` [S11]. Stripe says real shops also need webhooks, because a customer can close the browser after paying [S11]. For this sandbox dashboard a **Refresh** button and the `refresh_statuses` command cover that (same choice as rnd/011 for Wise).
- **Amounts are integers in the minor unit** (sen): RM 10.00 → `1000` [S10]. Minimum RM 2.00 [S10].
- **Errors have one shape**: `error.type`, `error.code`, `error.message`, `error.param` [S7]. Card declines happen **inside** hosted Checkout, so our API calls rarely see them.
- **Request ID:** Stripe returns a `Request-Id` header on responses (not on the pages above; check it in experiment 2). We store it in the API log like Wise's `x-trace-id`, so you can find the call in the Dashboard's request logs (Workbench).
- **Version:** pin `Stripe-Version: 2026-09-30.endive` so a Dashboard upgrade can't change our responses [S8].
- **FPX** (Malaysian online banking) appears in Checkout automatically for MYR once enabled in the Dashboard; no code [S12].

## Decision (what you will do and why)
1. Use **Stripe Checkout (hosted page)**, `mode=payment`, one line item built from the amount and description. Why: no card data in our app, no JavaScript, works with test cards and FPX [S4][S12].
2. Send the key as `Authorization: Bearer`, from `STRIPE_SECRET_KEY` in `.env`. Refuse live keys (`sk_live_`, `rk_live_`). Why: [S2][S3]; the project is sandbox-only.
3. Talk to Stripe with `requests` in **`payments/providers/stripe.py`**, the only Stripe file, next to `wise.py`; every call goes in the same API log with provider "Stripe". Why: rnd/012 Q3. *Alternative: the official `stripe` library; we skip it so both providers share one logging pattern.*
4. Save a `Payment` row with a UUID **before** creating the session; send that UUID as `Idempotency-Key`. Why: [S6], same rule as rnd/004.
5. Store `status` and `payment_status` as Stripe sends them; show one friendly label from the table above. Mark "paid" only when `payment_status == "paid"`. Why: [S5][S11].
6. Confirm by retrieving the session on return, plus a Refresh button and `refresh_statuses`. **No webhooks yet** (stretch goal with `stripe listen`). Why: no public URL needed in a sandbox [S11].
7. Currency **MYR**, amounts entered as decimals and converted to sen with `Decimal`. Why: the user is in Malaysia; RM 2.00 minimum [S10].
8. Pin `STRIPE_API_VERSION=2026-09-30.endive`. Why: [S8].

## Open questions
- Does the success redirect arrive before Stripe marks a card payment `paid`? (Experiment 3.) If not, the Refresh button covers it.
- Is FPX `paid` immediately at `complete`, or `unpaid` first? (Experiment 6.)
- Do we want refunds (`POST /v1/refunds`) and "expire session" buttons next? Not needed for the first demo.
