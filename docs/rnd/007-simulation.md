# 007 – Sandbox simulation endpoints
Date: 3 October 2026
Roadmap step: Step 0.5, Q9 (also Key fact 6; Step 0.6 rows 4, 11–13 and "Simulating before funding" / "Simulating two steps with no wait"; 02-dashboard-rnd F4 and 6.4)

## Question
- **Q9:** Which simulation transitions exist, in which order, and what must happen before the first one?
- Extra: every simulation endpoint with its exact method and path; does the path take the `/2026Q4` prefix; how long to wait between calls; is it sandbox-only; what happens if you call out of order or too fast?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Simulations (API reference) | https://docs.wise.com/api-reference/simulation | docs.wise.com | official doc | accessed 2026-10-03 | The full list of 19 simulation endpoints; "These features are limited to sandbox only" |
| S2 | Simulate transfer state change | https://docs.wise.com/api-reference/simulation/simulationtransferstatechange | docs.wise.com | official doc | accessed 2026-10-03 | Path, allowed transitions, "Fund the transfer first", "wait at least 5 seconds", responses `200`/`429`, security `UserToken`, sandbox URL with `/2026Q4` |
| S3 | Simulate a balance top-up | https://docs.wise.com/api-reference/simulation/simulationbalancetopup | docs.wise.com | official doc | accessed 2026-10-03 | Path, body fields, response fields, sandbox URL with `/2026Q4` |
| S4 | Simulate transfer payout failure | https://docs.wise.com/api-reference/simulation/simulationtransferpayoutfailure | docs.wise.com | official doc | accessed 2026-10-03 | Needs `bounced_back`; `400` "invalid input or transfer state" |
| S5 | Simulate a transfer delivery update | https://docs.wise.com/api-reference/simulation/simulationtransferdeliveryupdate | docs.wise.com | official doc | accessed 2026-10-03 | New in `2026Q4`; webhook only, no state change |
| S6 | Tracking transfers | https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses | docs.wise.com | official doc | 2026-09-04 | "Available statuses (must be called in order)"; fund first; wait 5 seconds |
| S7 | Testing refunds | https://docs.wise.com/guides/product/send-money/refunds/testing-refunds | docs.wise.com | official doc | 2026-09-16 | Same order; `funds_refunded` triggers `transfers#refund`; page mixes a `/v1` path line with `/2026Q4` examples on the production host |
| S8 | Payout failures | https://docs.wise.com/guides/product/send-money/tracking/payout-failures | docs.wise.com | official doc | 2026-09-04 | "You must create and fund a transfer" before testing; order up to `bounced_back` |
| S9 | Versioning | https://docs.wise.com/guides/developer/global-versioning | docs.wise.com | official doc | 2026-10-01 | The version goes in the URL path |
| S10 | OpenAPI file, 2026Q4 | https://docs.wise.com/_bundle/api-reference/@latest/index.json?download | docs.wise.com | official doc | accessed 2026-10-03 | Server `https://api.wise-sandbox.com/2026Q4`; `status` enum; example bodies; security per endpoint |
| S11 | Simulate transfer state change (Legacy) | https://docs.wise.com/api-reference/legacy/simulation/simulationtransferstatechange | docs.wise.com | official doc | accessed 2026-10-03 | Legacy path `GET /v1/simulation/transfers/{transferId}/{status}`; same rules |
| S12 | Sandbox & Production Environments | https://docs.wise.com/guides/developer/environments | docs.wise.com | official doc | 2026-09-04 | Sandbox supports "Simulate transfer state changes" and balance top-ups; more latency than production |
| S13 | Changelog | https://docs.wise.com/changelog | docs.wise.com | official doc | accessed 2026-10-03 | October 2026: delivery-update and settlement-funds simulations added. May 2026: payout-failure simulation; `funds_refunded` now triggers a refund webhook |
| S14 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 | The personal token's list of allowed actions does not mention simulation |
| S15 | Live check: paths without a token | https://api.wise-sandbox.com/2026Q4/simulation/transfers/1/processing | api.wise-sandbox.com | live check (curl, no token) | 2026-10-03 | `401` `missing_token` with `/2026Q4` or `/v1`; `404` with no version |
| S16 | teamSolutionAnalysts/wise-payment-gateway, `wiseUtil.ts` | https://github.com/teamSolutionAnalysts/wise-payment-gateway/blob/master/src/modules/wise/wiseUtil.ts | github.com | community GitHub | last commit 2022-10-07, 3 stars | Calls `/v1/simulation/transfers/{id}/{status}`. **Outdated:** legacy path |
| S17 | foss-fund/wise-banking-api-client, `sandbox_simulation.py` | https://github.com/foss-fund/wise-banking-api-client/blob/main/wise_banking_api_client/sandbox_simulation.py | github.com | community GitHub | last commit 2025-01-30, 0 stars | One method per transition. **Outdated:** host `api.sandbox.transferwise.tech`, `/v1`; says `funds_refunded` "will not trigger a refund webhook", no longer true [S13] |
| S18 | transferwise/public-api-postman-collection | https://github.com/transferwise/public-api-postman-collection | github.com | official GitHub | last commit 2024-07-24, 47 stars | Wise's old collection has all five transitions and the top-up. **Outdated:** `/v1` paths, `api.sandbox.transferwise.tech` |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**

Already checked **without a token** on 3 October 2026 [S15]:

| Request | Result |
|---|---|
| `GET https://api.wise-sandbox.com/2026Q4/simulation/transfers/1/processing` | `401` `missing_token` (path exists) |
| `GET https://api.wise-sandbox.com/v1/simulation/transfers/1/processing` (legacy) | `401` `missing_token` |
| `GET https://api.wise-sandbox.com/simulation/transfers/1/processing` (no version) | `404` `Resource not found` |
| `POST https://api.wise-sandbox.com/2026Q4/simulation/balance/topup` | `401` `missing_token` |
| `GET https://api.wise-sandbox.com/2026Q4/simulation/transfers/1/not_a_status` | `404` `Resource not found` |

All paths below go after `{{base_url}}/{{api_version}}` (= `https://api.wise-sandbox.com/2026Q4`). Header: `Authorization: Bearer <your-token>`. Use the **sandbox** host only.

1. **Token check (top-up):** `POST /simulation/balance/topup` with `{"profileId": <profileId>, "balanceId": <GBP balanceId>, "currency": "GBP", "amount": 1000}`. Paste code + body. If you get `401` or `403`: stop, paste the body, tell Claude.
2. **Before funding (transfer A):** create a transfer, do not fund it. `GET /simulation/transfers/{transferId}/processing`. Paste code + body. Then `GET /transfers/{transferId}`; paste `status`.
3. **Happy path (transfer B):** create and fund it (note 005). `GET /transfers/{transferId}`; paste `status`.
4. `GET /simulation/transfers/{transferId}/processing`. Paste code + body.
5. Wait 5+ seconds. `GET /simulation/transfers/{transferId}/funds_converted`. Paste.
6. Wait 5+ seconds. `GET /simulation/transfers/{transferId}/outgoing_payment_sent`. Paste. Then `GET /transfers/{transferId}`; paste `status`.
7. **Unhappy path (B):** wait 5+ s, `.../bounced_back`; wait 5+ s, `.../funds_refunded`. After each, `GET /transfers/{transferId}`; paste `status`. Then check your GBP balance.
8. **Too fast (transfer C, funded):** call `.../processing`, then `.../funds_converted` at once. Paste both. Wait 10 s, `GET /transfers/{transferId}`; paste `status`.
9. **Out of order (transfer D, funded, after `.../processing` and a 5 s wait):** call `.../outgoing_payment_sent` (skipping `funds_converted`). Paste code + body.
10. **Status not in the list:** `GET /simulation/transfers/{transferId}/cancelled`. Paste code + body.

Example from docs [S10] (top-up response), not from your account:
```json
{"transactionId": 5, "state": "COMPLETED", "balancesAfter": [{"id": 5, "value": 100, "currency": "EUR"}]}
```
Example from docs [S10] (state change response, shortened), not from your account: `{"id": 15574445, ..., "status": "processing", ...}`

## Finding (in your own words)
**Transitions and order** [S2][S6]: each step is allowed only from the step before it.

| Call `GET /simulation/transfers/{transferId}/<status>` with | Allowed from |
|---|---|
| `processing` | `incoming_payment_waiting` |
| `funds_converted` | `processing` ("Refer to regional guides for special regional requirements") |
| `outgoing_payment_sent` | `funds_converted` |
| `bounced_back` | `outgoing_payment_sent` |
| `funds_refunded` | `bounced_back` |

- **Before the first call: fund the transfer.** "Fund the transfer first before calling any simulation endpoints" [S2][S6][S8].
- **Even if funding already moved it to `processing`, you must still call `/processing`** [S2][S7].
- **Wait at least 5 seconds between calls.** "Although the simulation request may respond immediately, processing is asynchronous" [S2][S6]. The sandbox is also slower than production [S12].
- Not supported for email transfers [S2]. **Sandbox only** [S1].
- Simulating `funds_refunded` sends a `transfers#refund` webhook with a simulated amount [S2][S7].
- The only `status` values allowed are those five [S10]. There is no simulation for `cancelled`, `charged_back` or `unknown` (see note 006).

**Version prefix: yes.** Docs write the path as `/simulation/...` with "Version: 2026Q4" [S2]. The page's sandbox example is `https://api.wise-sandbox.com/2026Q4/simulation/transfers/{transferId}/{status}` [S2], and the API file's sandbox server is `https://api.wise-sandbox.com/2026Q4` [S10][S9]. The old form is `/v1/simulation/...` [S11]. Without any version you get `404` [S15].

**All 19 simulation endpoints** [S1] (each goes after `/2026Q4`):

| Method + path | What it does | Needed for us? |
|---|---|---|
| `GET /simulation/transfers/{transferId}/{status}` | Moves a transfer to the next status [S2] | **Yes** |
| `POST /simulation/balance/topup` | Adds fake money. Body: `profileId`, `balanceId`, `currency` (same as the balance), `amount`; optional `channel` `TRANSFER` or `CARD` (default `CARD`). `state` is always `COMPLETED` [S3] | **Yes** |
| `POST /simulation/transfers/{transferId}/payout-failure` | Sends a `transfers#payout-failure` webhook. Transfer must be `bounced_back` [S4] | Only with webhooks |
| `POST /simulation/transfers/{transferId}/delivery-update` | Sends a `transfers#delivery-update` webhook. New in `2026Q4`; no state change; needs a webhook subscription [S5] | Only with webhooks |
| `POST /simulation/verify-profile`, `POST /simulation/profiles/{profileId}/verifications` | Set profile verification to `PASSED` [S1] | No |
| `POST /simulation/profiles/{profileId}/bank-transactions/import`, `POST /simulation/profiles/{profileId}/swift-in` | Incoming bank / Swift payment into account details [S1] | No |
| `POST /simulation/settlement/funds`, `POST /simulation/sanction-cases` | Partner settlement; sanction cases [S1] | No |
| `GET /simulation/profiles/{profileId}/kyc-reviews/{kycReviewId}/requirements`, and `POST` `.../requirements/add`, `.../requirements/submit`, `.../verify` | KYC review testing [S1] | No |
| `POST /simulation/spend/profiles/{profileId}/cards/{cardToken}/transactions/authorisation`, `.../clearing`, `.../reversal`; `GET .../transactions`; `POST .../production` | Card testing [S1] | No |

**Out of order or too fast:** not documented for the state-change endpoint. Its page lists only `200` ("Transfer with updated status") and `429` (rate limit, with `Retry-After`) [S2]. Only the payout-failure page documents a `400` for a wrong transfer state [S4]. Steps 2, 8, 9 and 10 will show the real behaviour.

**Token risk:** the API file lists `UserToken` (OAuth) as the only security for the transfer and top-up simulations [S10]. Funding lists `UserToken, PersonalToken`. The personal token page does not mention simulation [S14]. So it is **not documented** that your personal token may call these endpoints. Step 1 checks this first.

**Doc traps:** the refunds guide says `GET /v1/simulation/...` in one line but uses `/2026Q4` in its examples [S7]. Guide examples also use the production host `api.wise.com` [S7]. Copy the path, never the host.

**Community code** uses the same five transitions in the same order, but on `/v1` paths and old hosts [S16][S17][S18].

Roadmap risk (not a contradiction): Key fact 6 and Step 0.6 assume your personal token can call the simulation API. The docs list only `UserToken` for it [S10]. Unverified until step 1.

Roadmap correction: none. Key fact 6, Step 0.6 rows 11–13 and 02-dashboard-rnd F4 match the live docs (order, "fund first", 5 seconds, `/processing` still needed). 02-dashboard-rnd F4 is just missing the newer payout-failure and delivery-update simulations [S4][S5][S13].

## Decision (what you will do and why)
1. **Use `https://api.wise-sandbox.com/2026Q4/simulation/...`.** Why: same version as every other call; legacy `/v1` is for old code [S9][S11].
2. **Show the sandbox panel only when the app's environment setting is "sandbox".** Why: these endpoints are sandbox-only [S1].
3. **The panel offers only the one valid next step** (table above), and "Fund" before any of them. Why: each step is allowed only from the previous one [S2].
4. **Save every simulation call** (transfer, target status, time, HTTP code). Why: it answers the 02-dashboard-rnd 6.4 question "was `/processing` already called?", even when funding already shows `processing`.
5. **Block the next simulation button for 5 seconds after the last call.** Why: Wise says to wait at least 5 seconds [S2].
6. **After each simulation, read the status with `GET /transfers/{transferId}`.** Why: processing is asynchronous, so the simulation reply may be early [S2]. Proposed — confirm after the experiment.
7. **Use the top-up only for the balance in the transfer's source currency.** Why: `currency` must match the balance [S3].
8. **Skip the other 15 endpoints.** Payout-failure and delivery-update only if Phase 5.2 (webhooks) happens. Why: out of scope.
9. **Proposed — confirm after the experiment:** if step 1 shows the personal token cannot call simulations, stop and re-plan with Claude (and ask `api@wise.com`, as in Step 0.3). Why: the whole demo depends on it.

## Open questions
- Can a personal token call the simulation endpoints at all (step 1)?
- What does the state-change call return when called before funding, out of order, too fast, or with a status not in the list? Not documented [S2].
- After a real funding call, is the status already `processing`? If so, does `/processing` still return `200`?
- After `funds_refunded`, is the GBP balance refunded in full? The docs say "Balances and the sandbox UI will always reflect the full refund amount" [S2].
- `funds_converted` mentions "special regional requirements" [S2]. Do any apply to GBP → EUR? Not stated.
