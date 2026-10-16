# 004 – customerTransactionId and idempotency
Date: 3 October 2026
Roadmap step: Step 0.5, Q5 (also Step 0.6 "break it" test 4, and Phase 3.3)

## Question
- **Q5:** What does `customerTransactionId` do? What happens if you send the same one twice?
- Also: which format; what Wise returns on a repeat (same body or a different body); how it helps after a timeout; other Wise idempotency mechanisms; when our app should make and save the ID.

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Create a transfer | https://docs.wise.com/api-reference/standard-transfer/transfercreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Field is a required string; "treated as repeat messages and will not create duplicate transfers"; retry limit with back-off |
| S2 | Create standard transfers | https://docs.wise.com/guides/product/send-money/standard-api-transfers | docs.wise.com | official doc | accessed 2026-10-03 | Example body with a UUID value |
| S3 | Transfer errors | https://docs.wise.com/guides/developer/errors/transfers | docs.wise.com | official doc | accessed 2026-10-03 | "A new identifier represents a different logical transfer"; `quote.duplicate`; retry rules |
| S4 | Handle API errors | https://docs.wise.com/guides/developer/errors | docs.wise.com | official doc | accessed 2026-10-03 | "A timeout … does not prove that Wise rejected the request"; what to do with 408 and 5xx |
| S5 | Getting started with Wise API, "Idempotency" | https://docs.wise.com/guides/developer | docs.wise.com | official doc | accessed 2026-10-03 | Idempotency is per endpoint; header `X-idempotence-uuid` vs body `customerTransactionId` |
| S6 | Create a Balance Account | https://docs.wise.com/api-reference/balance/balancecreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `X-idempotence-uuid` header is **required** |
| S7 | Convert or Move Money Between Balances | https://docs.wise.com/api-reference/balance/balancemovement | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `X-idempotence-uuid` header is required |
| S8 | Balance accounts (guide) | https://docs.wise.com/guides/product/accounts/balance-accounts | docs.wise.com | official doc | accessed 2026-10-03 | Example create-balance request with the header |
| S9 | Create batch group transfer | https://docs.wise.com/api-reference/batch-group/batchgrouptransfercreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Batch transfers use `customerTransactionId` too |
| S10 | Fund a Transfer | https://docs.wise.com/api-reference/transfer/transferfund | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | No idempotency field; 409 `PaymentAlreadyExistsError`; error code `payment.exists` |
| S11 | Funding errors | https://docs.wise.com/guides/developer/errors/funding | docs.wise.com | official doc | accessed 2026-10-03 | `payment.exists`: "Reconcile the existing payment … instead of creating another payment" |
| S12 | Correlation ID | https://docs.wise.com/guides/developer/headers/correlation-id | docs.wise.com | official doc | accessed 2026-10-03 | `X-External-Correlation-Id` is "a simple echo"; Wise does not store it |
| S13 | List transfers | https://docs.wise.com/api-reference/standard-transfer/transferlist | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Filters: `profile`, `status`, dates, `limit`, `offset`; items include `customerTransactionId` |
| S14 | Profile errors | https://docs.wise.com/guides/developer/errors/profiles | docs.wise.com | official doc (partner endpoint) | accessed 2026-10-03 | Profile creation: optional `X-idempotence-uuid`; 409 if a matching profile exists |
| S15 | Transfers (API reference overview) | https://docs.wise.com/api-reference/transfer | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `PUT /transfers/{transferId}/cancel` while `incoming_payment_waiting` |
| S16 | transferwise/api-docs `_transfers.md` | https://github.com/transferwise/api-docs/blob/master/source/includes/reference/_transfers.md | github.com | official GitHub, **outdated**: repo archived 2020-11-19; uses `api.sandbox.transferwise.tech` and `/v1` | archived 2020-11-19; 11 stars | Old docs gave the field type as "UUID" |
| S17 | uuid — UUID objects | https://docs.python.org/3/library/uuid.html | docs.python.org | official doc | page updated 2026-10-02 (Python 3.14) | `uuid4()` = random UUID; `uuid1()` "may compromise privacy" |
| S18 | Database transactions (Django 6.1) | https://docs.djangoproject.com/en/stable/topics/db/transactions/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | Autocommit: "Each query is immediately committed"; "keep your transactions as short as possible" |
| S19 | foss-fund/wise-banking-api-client `model/transfer.py` | https://github.com/foss-fund/wise-banking-api-client/blob/main/wise_banking_api_client/model/transfer.py | github.com | community GitHub, **outdated**: `api.sandbox.transferwise.tech`, `/v1/transfers` | last commit 2025-01-30; 0 stars | Makes a new UUID by default for each new request object |
| S20 | tedchou12/transferwise `tw_api.py` | https://github.com/tedchou12/transferwise/blob/master/tw_api.py | github.com | community GitHub, **outdated**: `api.transferwise.com/v1/transfers` | last commit 2021-02-28; 1 star | Makes `str(uuid.uuid4())` inside the create-transfer call |
| S21 | LarsArtmann/wise-go `transfers.go` | https://github.com/LarsArtmann/wise-go/blob/master/transfers.go | github.com | community GitHub; uses `api.wise-sandbox.com` but legacy `/v1/transfers` | last commit 2026-10-01; 1 star | Claims a repeat "will return the existing transfer" (no test or source in the repo) |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**
Before you start: do note 003 steps 1–6, so you have a patched `quote_id` and a `recipient_id`. Do **not** fund anything here.
Every request: header `Authorization: Bearer <your-token>`, prefix `{{base_url}}/{{api_version}}`.
1. Make one UUID in a terminal: `python3 -c "import uuid; print(uuid.uuid4())"` [S17]. Save it in Postman as a fixed value `ctid`. Do not let Postman make a new value on each send.
2. **A – first send:** `POST /transfers`, body `{"targetAccount": <recipient_id>, "quoteUuid": "<quote_id>", "customerTransactionId": "<ctid>", "details": {"reference": "R&D 004"}}` [S1]. Paste HTTP status, `id`, `customerTransactionId`, `status`, `created`.
3. **B – exact repeat:** send the same request again. Paste HTTP status and body. Same `id` as A? Same `created`?
4. **C – same ID, different body:** change only `details.reference` to `"R&D 004 changed"`. Paste status and body. Did the reference change?
5. **D – new ID, same quote:** make a new UUID, keep the same quote. Paste status and body.
6. **E – same ID, new quote:** create and PATCH a fresh quote. Send with the **old** `ctid` and the new quote. Paste status and body.
7. **F (optional) – not a UUID:** fresh quote, `customerTransactionId: "test-1"`. Paste status and body.
8. **Count:** `GET /transfers?profile={profileId}&createdDateStart=<today>` [S13]. Paste `id`, `customerTransactionId`, `quoteUuid` of today's transfers. How many carry `ctid`?
9. **Clean up:** `PUT /transfers/{transferId}/cancel` for each test transfer [S15]. Paste the new `status`.
10. **Other endpoint (only if you need a new currency balance):** `POST /profiles/{profileId}/balances` once **without** `X-idempotence-uuid` (paste the response), then twice **with the same** new UUID [S6]. Paste both responses.

Fill this table: | Test | HTTP code | Transfer `id` | Error `code` (if any) | New transfer created? |

Example from docs [S3], not from your account (one quote used twice):
```json
{ "timestamp": "2026-08-21T10:01:31.407453801Z",
  "errors": [ { "code": "quote.duplicate", "message": "Cannot use one quote to create 2 transfers", "arguments": [] } ] }
```

## Finding (in your own words)
**Direct answer.** `customerTransactionId` is *your* ID for "one payment I mean to make". It is a required field in `POST /transfers` [S1]. If the first call fails or times out, you retry with the same value. Wise then treats the retry as a repeat and does **not** create a second transfer [S1].
- **Same ID = same payment. New ID = new payment. Make the ID once, save it, and reuse it for every retry.**
- "A new identifier represents a different logical transfer and can create a duplicate" [S3].

**What comes back on a repeat? The docs do not say.** They promise "no duplicate", but they do not say if you get the same transfer back (200) or an error. One community SDK claims "will return the existing transfer", without a test or source [S21]. If the body is different (tests C, E), the docs say nothing. Only tests B, C, E can answer this.

**Format.**
- The 2026Q4 reference says only "string", "Unique identifier randomly generated per transfer request by the calling client" [S1]. Every example is a UUID [S1][S2].
- The old official docs (archived 2020) gave its type as "UUID" [S16]. Use a random UUID (version 4) [S17].
- "Per transfer request" means per payment you intend, not per HTTP send. Wise: "Reuse it when retrying the same uncertain creation attempt" [S3].

**A second safety net: one quote = one transfer.** A second transfer from a used quote fails with 400 `quote.duplicate` [S3] (example above; it sits under the third-party transfer heading). But a **new quote plus a new ID** is a new transfer. That is how a double payment happens.

**After a timeout.** "A timeout or connection failure does not prove that Wise rejected the request" [S4].

| What really happened at Wise | What you see | Retry with the **same** ID gives |
|---|---|---|
| Request never arrived | Timeout | One transfer, created now [S1] |
| Transfer created, reply lost | Timeout | No second transfer [S1] |

- Use the endpoint's idempotency mechanism, or check if the first call worked, before you retry [S4].
- Do not tell the user it failed while the outcome is unknown [S4]. A 408 or 5xx alone does not prove the call can be repeated safely [S4].
- Retry a limited number of times, with back-off [S1][S3]. Then reconcile [S3]: list transfers by `profile` and date and look for your ID. There is no filter by ID [S13].

**Everyday analogy.** You phone a pizza shop and give your order number, 42. The line drops. You call again and say "order 42". The shop sees 42 is already in the oven and does not make a second pizza. If you invent a new number, you get two pizzas. Doing the same thing twice with the same result is called **idempotency**.

**Other Wise endpoints.** "Idempotency applies to specific endpoints … rather than globally" [S5].

| Endpoint | Mechanism | Required? |
|---|---|---|
| `POST /transfers` | `customerTransactionId` in body | Yes [S1] |
| `POST /profiles/{profileId}/batch-groups/{batchGroupId}/transfers` | `customerTransactionId` in body | Yes [S9] |
| `POST /profiles/{profileId}/balances` | `X-idempotence-uuid` header | Yes [S6][S8] |
| `POST /profiles/{profileId}/balance-movements` | `X-idempotence-uuid` header | Yes [S7] |
| Create a card order | `X-idempotence-uuid` header | Named in [S5] |
| Profile creation (partner flow) | `X-idempotence-uuid` header | Not stated; 409 if a matching profile exists [S14] |
| `POST /profiles/{profileId}/transfers/{transferId}/payments` | No key. A second payment is refused: 409 / `payment.exists` | — [S10][S11] |

- `X-External-Correlation-Id` is **not** idempotency. It is "a simple echo. Wise does not log or store this value" [S12].

**Roadmap corrections:**
- Roadmap correction: Step 0.6 request 3 (`POST /profiles/{profileId}/balances`) must send the header `X-idempotence-uuid`. It is required [S6][S8]. The roadmap does not mention it.
- Roadmap correction: Phase 7 table says Wise duplicate protection = `customerTransactionId`. That is true only for transfers. Balances use the `X-idempotence-uuid` header; funding has no key and answers 409 [S5][S6][S10].

**Community evidence.** S20 makes a new UUID inside the create-transfer call, so a retry through that call sends a new ID. S19 makes a new UUID for each new request object unless you pass one. Both show the trap: **the ID must come from storage, not be made at send time.**

## Decision (what you will do and why)
1. Make the UUID (`uuid4`) once per payment, when the user presses "Create transfer". Why: one ID per logical transfer [S3]; `uuid4` is random [S17].
2. Save it in our transfer row, with quote ID and recipient ID, **before** calling Wise, and let that save commit. Why: retries, even after a crash, must send the same ID [S1]. Django commits each query at once in autocommit mode [S18].
3. Do not keep a database transaction open during the Wise call. Why: "keep your transactions as short as possible" [S18].
4. Make the column unique. Why: one row per intended payment, enforced by the database.
5. Retry = same row, same ID, same quote, same recipient, same body. Retry a few times with back-off. Never a new ID for a retry. Why: [S1][S3][S4].
6. If still unknown after retries: mark the row "needs check", do not show "failed", and reconcile with `GET /transfers` [S4][S13].
7. If a repeat returns the same transfer, store its `id` once (update, not insert). If it returns an error, treat that code as "maybe already created → reconcile". **Proposed — confirm after the experiment (tests B, C, E).**
8. Funding: on 409 or `payment.exists`, reconcile instead of paying again. Why: [S10][S11].
9. Send `X-External-Correlation-Id` for the API log only, never for duplicate protection. Why: [S12].

## Open questions
- What exactly does Wise return for tests B, C and E? The docs do not say.
- How long does Wise remember a `customerTransactionId`? Is it unique per profile or per user? Is there a length limit? Is a non-UUID accepted (test F)?
- Does `quote.duplicate` apply to standard `POST /transfers`? The docs list it under third-party transfers [S3].
- Cancel: the reference says `PUT /transfers/{transferId}/cancel` [S15], but the transfer errors guide shows `POST` [S3]. Record which one works.
- stackoverflow.com blocked my tool. Through the Stack Exchange API I found no question about duplicate `customerTransactionId`.
