# 003 – Send-money flow: order of steps, IDs, and the quote PATCH
Date: 3 October 2026
Roadmap step: Step 0.5, Q3 and Q4 (also Step 0.6 requests 5–10, and Phase 4.5 wizard)

## Question
- **Q3:** What order do you create quote, recipient and transfer in? Which ID from each step does the next step need?
- **Q4:** Why do you update ("PATCH") a quote with the recipient before creating the transfer?
- Also: how long a quote and its rate last, and what happens after expiry; authenticated vs unauthenticated quotes; `sourceAmount` vs `targetAmount`.

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Send money | https://docs.wise.com/guides/product/send-money | docs.wise.com | official doc | accessed 2026-10-03 | The four steps: quote, recipient, transfer, fund |
| S2 | Quote creation | https://docs.wise.com/guides/product/send-money/quotes | docs.wise.com | official doc | accessed 2026-10-03 | Authenticated vs unauthenticated table; rate "typically remains valid for 30 minutes"; sandbox rates not live |
| S3 | Authenticated Quotes | https://docs.wise.com/guides/product/send-money/quotes/authenticated-quote | docs.wise.com | official doc | accessed 2026-10-03 | Send `sourceAmount` OR `targetAmount`; `expirationTime` vs `rateExpirationTime`; quote statuses; sample response |
| S4 | Create a quote (unauthenticated) | https://docs.wise.com/api-reference/quote/quotecreateunauthenticated | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `POST /quotes`; no token needed; "has no ID and can't be used to create a transfer" |
| S5 | Update a quote (guide) | https://docs.wise.com/guides/product/send-money/quotes/update-quote | docs.wise.com | official doc | accessed 2026-10-03 | Why the PATCH matters; what can change |
| S6 | Create a quote (authenticated) | https://docs.wise.com/api-reference/quote/quotecreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Request/response fields; `targetAccount` as alternative to PATCH; how to pick the right `paymentOption` |
| S7 | Update a quote (API reference) | https://docs.wise.com/api-reference/quote/quoteupdate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `PATCH` path; body `targetAccount`; body type `application/merge-patch+json`; `payOut` may change |
| S8 | Retrieve a quote by ID | https://docs.wise.com/api-reference/quote/quoteget | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Expired = not used within 30 minutes; still readable for about 48 hours |
| S9 | Payouts for small-to-medium businesses (SMBs) | https://docs.wise.com/guides/product/send-money/use-cases/payouts-smbs | docs.wise.com | official doc | accessed 2026-10-03 | The 7-step order for personal tokens; funding by API only in US, CA, AU, NZ, SG, MY |
| S10 | Transfers (guide) | https://docs.wise.com/guides/product/send-money/transfers | docs.wise.com | official doc | accessed 2026-10-03 | Before a transfer: check transfer requirements and update the quote |
| S11 | Retrieve recipient account requirements dynamically | https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Needs the quote ID; `Accept-Minor-Version: 1` for new integrations; a quote-less variant exists |
| S12 | Create a recipient account | https://docs.wise.com/api-reference/recipient/recipientcreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `POST /accounts`; body field `profile`; response `id` (integer) |
| S13 | Validate transfer requirements | https://docs.wise.com/api-reference/transfer/transferrequirementsvalidate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `POST /transfer-requirements` needs `targetAccount` + `quoteUuid` |
| S14 | Create a transfer | https://docs.wise.com/api-reference/standard-transfer/transfercreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Body fields; one transfer per quote; response `id` and `status`; `sourceAccount` = refund recipient |
| S15 | Create standard transfers | https://docs.wise.com/guides/product/send-money/standard-api-transfers | docs.wise.com | official doc | accessed 2026-10-03 | Example create-transfer request (quoted below) |
| S16 | Transfers (API reference overview) | https://docs.wise.com/api-reference/transfer | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Unfunded transfers cancelled after about 14 days; `PUT /transfers/{transferId}/cancel` |
| S17 | Fund a Transfer | https://docs.wise.com/api-reference/transfer/transferfund | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Fund path; `CREATED`/`COMPLETED`/`REJECTED`; SCA "most likely" for UK/EEA |
| S18 | Funding a transfer | https://docs.wise.com/guides/product/send-money/funding | docs.wise.com | official doc | accessed 2026-10-03 | Fund "as soon as possible" so FX rates do not expire; fund the amount from the final quote |
| S19 | Fund transfers from your Wise balance | https://docs.wise.com/guides/product/send-money/funding/fund-from-balance | docs.wise.com | official doc | accessed 2026-10-03 | Body `{"type": "BALANCE"}`; sample responses |
| S20 | Quote errors | https://docs.wise.com/guides/developer/errors/quotes | docs.wise.com | official doc | accessed 2026-10-03 | `error.quote.amount.onlySingle`; PATCH on expired quote = 422 `error.quote.expired` |
| S21 | Transfer errors | https://docs.wise.com/guides/developer/errors/transfers | docs.wise.com | official doc | accessed 2026-10-03 | `error.quote.expired`, `quote.duplicate`, `error.quote.accept.noTargetAccount` (listed under the third-party transfer heading) |
| S22 | Create quote (correspondent guide), "Timing rules" | https://docs.wise.com/guides/product/send-money/use-cases/correspondent/correspondent-create-auth-quote | docs.wise.com | official doc (written for correspondent partners) | accessed 2026-10-03 | Rate held 24–48 h after the transfer exists; recipient-first flow needs no PATCH |
| S23 | foss-fund/wise-banking-api-client (README) | https://github.com/foss-fund/wise-banking-api-client | github.com | community GitHub, **outdated**: uses `sandbox.transferwise.tech` and legacy `/v3/…`, `/v1/…` paths | last commit 2025-01-30; 0 stars | A real client follows the same order: quote → requirements → recipient → update quote → transfer → fund |
| S24 | Stack Overflow Q79548340 "Wise (Transferwise) API to create a transfer" (read through the Stack Exchange API; stackoverflow.com blocked my tool) | https://api.stackexchange.com/2.3/questions/79548340/answers?site=stackoverflow&filter=withbody | api.stackexchange.com | SO, **outdated**: uses `api.sandbox.transferwise.tech/v1/transfers` | asked 2025-04-01 | A wrong `sourceAccount` gave a confusing 404 `not.found` |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**
Every request: header `Authorization: Bearer <your-token>`, prefix `{{base_url}}/{{api_version}}` (= `https://api.wise-sandbox.com/2026Q4`).
1. `POST /profiles/{profileId}/quotes`, body `{"sourceCurrency": "GBP", "targetCurrency": "EUR", "sourceAmount": 100, "targetAccount": null}` [S3].
   Paste: `id`, `rate`, `sourceAmount`, `targetAmount`, `payOut`, `status`, `createdTime`, `expirationTime`, `rateExpirationTime`, `providedAmountType`, and the one `paymentOptions` item with `"payIn": "BALANCE"` (its `fee.total`, `price.total.value.amount`, `formattedEstimatedDelivery`, `disabled`).
2. Same request with `"targetAmount": 100` instead of `sourceAmount`. Paste `providedAmountType`, `sourceAmount`, `targetAmount`. Then send **both** amounts. Paste the error.
3. `GET /quotes/{quoteId}/account-requirements` with header `Accept-Minor-Version: 1` [S11]. Paste the `type` values (details belong in note 008).
4. `POST /accounts` with `profile`, `currency: "EUR"`, `type`, `accountHolderName`, `details` (fields from step 3) [S12]. Paste `id`.
5. `PATCH /profiles/{profileId}/quotes/{quoteId}`, header `Content-Type: application/merge-patch+json`, body `{"targetAccount": <recipient id>}` [S7].
   Paste the same fields as step 1. Fill a **before/after table** (step 1 vs step 5).
6. `POST /transfer-requirements`, body `{"targetAccount": …, "quoteUuid": "…", "details": {"reference": "R&D 003"}}` [S13]. Paste the field names it returns.
7. `POST /transfers` (body like the example below) [S14]. Paste `id`, `status`, `quoteUuid`, `rate`, `sourceValue`, `targetValue`.
8. `GET /profiles/{profileId}/quotes/{quoteId}`. Paste `status` (the guide says it should be `ACCEPTED` [S3]).
9. `POST /profiles/{profileId}/transfers/{transferId}/payments`, body `{"type": "BALANCE"}` [S19]. Paste the whole response. A UK profile with a personal token may be refused (see 02-dashboard-rnd, E2).
10. Expiry test: make a new quote, wait until after its `expirationTime`, then (a) PATCH it, (b) `POST /transfers` with it. Paste both HTTP codes and error bodies.
11. `POST /quotes` with **no** `Authorization` header, same body as step 1. Paste whether the response has an `id`.

Example from docs [S3], not from your account (fields cut; the times are from 2019):
```json
{ "id": "11144c35-9fe8-4c32-b7fd-d05c2a7734bf", "rate": 1.30445, "createdTime": "2019-04-05T13:18:58Z",
  "rateType": "FIXED", "rateExpirationTime": "2019-04-08T13:18:57Z", "providedAmountType": "SOURCE",
  "status": "PENDING", "expirationTime": "2019-04-05T13:48:58Z" }
```
Example from docs [S15], not from your account (create-transfer body):
```json
{ "targetAccount": 8692237, "quoteUuid": "8fa9be20-ba43-4b15-abbb-9424e1481050",
  "customerTransactionId": "54a6bc09-cef9-49a8-9041-f1f0c654cd88", "details": { "reference": "Invoice 2026-001" } }
```

## Finding (in your own words)
**Q3 – order.** Quote → recipient → update quote → transfer → fund [S1][S9]. Wise's personal-token guide lists 7 calls [S9]:

| # | Step | Method + path | IDs it needs | IDs / values it produces |
|---|---|---|---|---|
| 1 | Create quote | `POST /profiles/{profileId}/quotes` | `profileId` | quote `id` (UUID text), `rate`, fees per payment option, `expirationTime`, `rateExpirationTime` [S6] |
| 2 | Recipient requirements | `GET /quotes/{quoteId}/account-requirements` | `quoteId` | list of account types and their fields [S11] |
| 3 | Create recipient | `POST /accounts` | `profileId` (as body field `profile`) | recipient `id` (integer) [S12] |
| 4 | Update quote | `PATCH /profiles/{profileId}/quotes/{quoteId}` | `profileId`, `quoteId`, recipient `id` as `targetAccount` | same quote `id`, updated `payOut`, payment options, prices [S7] |
| 5 | Transfer requirements | `POST /transfer-requirements` | recipient `id` (`targetAccount`), quote `id` (`quoteUuid`) | extra fields needed in `details` [S13] |
| 6 | Create transfer | `POST /transfers` | `targetAccount`, `quoteUuid`, your `customerTransactionId` | transfer `id` (integer), `status: incoming_payment_waiting` [S14] |
| 7 | Fund | `POST /profiles/{profileId}/transfers/{transferId}/payments` | `profileId`, transfer `id` | `status` `COMPLETED`/`REJECTED`, `balanceTransactionId`; transfer moves to `processing` [S17][S19] |

- **Each step hands one ID to the next: quote `id` → recipient `id` → transfer `id`. `profileId` is in almost every call.**
- One quote can make only one transfer [S14]. Use `quoteUuid`. The old integer field `quote` is "V1 quote ID" [S14].
- Do not send `sourceAccount`. It is the refund recipient [S14]. One SO user got a 404 `not.found` from a wrong `sourceAccount` [S24].
- Another valid order is "recipient first": put `targetAccount` in the create-quote body, and then no PATCH is needed [S6][S22].
- Funding by API with a personal token works only for accounts in US, CA, AU, NZ, SG, MY. Others fund in the Wise website [S9].

**Q4 – why PATCH.** The recipient can change the price. Example from Wise: USD to a country outside the USA uses international networks and costs more [S5][S7].

| What can change after the PATCH | Source |
|---|---|
| `payOut` (e.g. to `SWIFT` or `INTERAC`, depending on recipient type) | [S7] |
| Available payment options (`paymentOptions`) | [S5][S7] |
| Prices / fees | [S5][S7] |
| Estimated delivery times | [S5][S7] |
| The amount you must fund ("the amount provided in the final quote object") | [S18] |

- **Show the customer the price from the patched quote, not the first quote.** If the price changed, tell the customer before they confirm [S7].
- Show `price.total.value.amount` of the payment option that matches the quote's `payOut` and your `payIn` [S6].
- The docs do **not** say that the rate or `expirationTime` change after the PATCH. The experiment will show.

**Expiry and rate lock.**
- The rate is locked when the quote is created and "typically remains valid for 30 minutes" [S2]. A quote not used for a transfer within 30 minutes counts as expired [S8].
- There are two times: `expirationTime` = create the transfer before this; `rateExpirationTime` = when the locked rate ends [S3].
- After the transfer exists, the correspondent guide says the rate is held 24–48 hours; fund before `rateExpirationTime` or the rate "will float" [S22].
- Expired quote: PATCH gives 422 `error.quote.expired` [S20]. Create transfer gives 400 `error.quote.expired`, "Sorry, your quote has expired. Please get a new one." [S21]. Fix: new quote, then redo the requirement checks [S22].
- An unfunded transfer is cancelled after about 14 days [S16]. Sandbox rates are "realistic but not live" [S2].

**Authenticated vs unauthenticated** [S2][S4]:

| | Authenticated `POST /profiles/{profileId}/quotes` | Unauthenticated `POST /quotes` |
|---|---|---|
| Token / profile | Required | Not required |
| Quote ID / rate lock | Yes / yes | No / no |
| Can create a transfer | Yes | No (display only) |

**`sourceAmount` vs `targetAmount`.** Send exactly one [S3]. Both → 400 `error.quote.amount.onlySingle` [S20].
- `sourceAmount` = "Amount to send". `targetAmount` = "Amount recipient should receive" [S3]. The response says which one you gave in `providedAmountType` [S6].
- The errors guide documents 422 `error.quote.targetAmount.notSupported.volatility.partner`: "Send sourceAmount instead" [S20].

**Roadmap corrections:**
- Roadmap correction: Step 0.6 (and 02-dashboard-rnd F1) skip **transfer requirements** (`POST /transfer-requirements`) between the PATCH and `POST /transfers`. Wise lists it as step 5 and says "Always call" it [S9][S14].
- Roadmap correction: Key fact 7 and 02-dashboard-rnd F6 say "rate locked for about 30 minutes". More exact: ~30 minutes is the deadline to **create the transfer** (`expirationTime`); the locked rate has its own `rateExpirationTime` [S3][S22]. The wizard's "refuse an expired quote" rule should use `expirationTime`.
- Roadmap correction: Step 0.6 request 6 should send `Accept-Minor-Version: 1` [S11]; request 8 sends its body as `application/merge-patch+json` [S7].
- Roadmap correction (for Q7, outside this note): 02-dashboard-rnd F3 says `transfer.insufficient_funds`. The 2026Q4 fund reference lists `balance.insufficient-funds`; the fund-from-balance guide still shows the old code [S17][S19].
- Docs typo: the PATCH reference text says "the recipient `sourceAccount` value", but the request field is `targetAccount` [S7]. Use `targetAccount`.

**Community evidence.** S23 uses the same order (quote, requirements, recipient, update quote, transfer, fund), but with retired hosts and legacy paths.

## Decision (what you will do and why)
1. Use the quote-first order, all 7 calls. Why: it is Wise's personal-token flow [S9], and requirements need a quote ID [S11].
2. Always PATCH, then read the price again from the PATCH response. Why: price, `payOut` and delivery can change [S5][S7].
3. Show `price.total.value.amount` of the option with `payIn` `BALANCE` and the quote's `payOut`. Why: Wise says to show this field [S6]. **Proposed — confirm after the experiment.**
4. Use `sourceAmount` in the MVP. Why: the user types how much GBP to send, and the funding balance is in GBP. Avoids the volatility error [S20].
5. Save quote `id`, `expirationTime` and `rateExpirationTime`. Block "Create transfer" after `expirationTime` and send the user back to step 1. Why: [S20][S21][S22].
6. Fund right after creating the transfer. Why: so the rate does not float [S18][S22].
7. Never send `sourceAccount`; use `quoteUuid`, not `quote`. Why: [S14][S24].
8. No unauthenticated quotes in this project. Why: they cannot create transfers [S4].

## Open questions
- Does the PATCH change `rate`, `targetAmount` or `expirationTime` for GBP → EUR (IBAN)? Only step 5 can show it.
- The personal-token page does not list "update quote", and the quote reference lists only `UserToken` security. The SMB guide still includes the PATCH [S9]. Does it work with your token?
- The create-quote reference says "set the `payIn` field to `BALANCE`", but the request schema only has `preferredPayIn` [S6]. Which one, if any?
- Is the 24–48 hour rate hold [S22] also true for a business account with a personal token?
- Quote status lists differ: guide says `PENDING/ACCEPTED/EXPIRED/CANCELLED` [S3]; reference enum says `PENDING/ACCEPTED/FUNDED/EXPIRED` [S6]. Record what you see in steps 8–9.
- `error.quote.expired` and `quote.duplicate` examples sit under the third-party transfer heading in [S21]. Are they the same for `POST /transfers`?
- The unauthenticated reference says "no ID", but its sample response shows an `id` [S4]. Step 11 decides.
- Pages were read through their `.md` versions (same URL + `.md`); the HTML pages also load (HTTP 200).
