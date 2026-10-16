# 005 – Funding a transfer
Date: 3 October 2026
Roadmap step: Step 0.5, Q6–Q7 (also Step 0.6 rows 2, 4, 10 and "Funding with too little balance"; 02-dashboard-rnd F3 and Experiment E2)

## Question
- **Q6:** Can you fund a transfer from a balance in a *different* currency?
- **Q7:** What does the funding call return when the balance is too low? What status is the transfer left in?
- Extra: Which funding methods exist via the API? Which countries may fund with a personal token, and does that rule apply in the sandbox? After how many days is an unfunded transfer cancelled?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Funding a transfer | https://docs.wise.com/guides/product/send-money/funding | docs.wise.com | official doc | 2026-09-04 | The four funding options; "We currently do not support cross-balance funding"; status goes `incoming_payment_waiting` → `processing` when funds arrive |
| S2 | Fund transfers from your Wise balance | https://docs.wise.com/guides/product/send-money/funding/fund-from-balance | docs.wise.com | official doc | 2026-09-04 | Endpoint and body; COMPLETED example; insufficient-funds example with `transfer.insufficient_funds`; transfer stays `incoming_payment_waiting` |
| S3 | Fund a Transfer (API reference, 2026Q4) | https://docs.wise.com/api-reference/transfer/transferfund | docs.wise.com | official doc | accessed 2026-10-03 | Security `UserToken, PersonalToken`; SCA note for UK/EEA; response fields; `status` and `errorCode` enums; "call this endpoint again" after a top-up |
| S4 | OpenAPI file, 2026Q4 | https://docs.wise.com/_bundle/api-reference/@latest/index.json?download | docs.wise.com | official doc | accessed 2026-10-03 | Exact example bodies under HTTP `201`, including "BALANCE - rejected (insufficient funds)" with `balance.insufficient-funds`; personal token "PSD2 restrictions apply for EU/UK users" |
| S5 | OpenAPI file, Legacy | https://docs.wise.com/_bundle/api-reference/@legacy/index.json?download | docs.wise.com | official doc | accessed 2026-10-03 | Legacy path `/v3/profiles/{profileId}/transfers/{transferId}/payments`; same `balance.insufficient-funds` example (2026Q3 and 2027Q1 Preview files say the same) |
| S6 | Funding errors | https://docs.wise.com/guides/developer/errors/funding | docs.wise.com | official doc | 2026-09-22 | Lists both insufficient-funds codes; "always check `status` and `errorCode`"; failures can also be non-2xx; `transfer.invalid-state`, `payment.exists`, `balance.no-balance-for-currency`; SCA `403` |
| S7 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 | What a personal token may do; API funding only for accounts based in US, Canada, Australia, New Zealand, Singapore, Malaysia |
| S8 | Payouts for small-to-medium businesses (SMBs) | https://docs.wise.com/guides/product/send-money/use-cases/payouts-smbs | docs.wise.com | official doc | 2026-09-04 | Same six countries; "subject to regional regulatory requirements that might change"; other accounts "Log into the Wise account to fund the transfer" |
| S9 | Transfers (API reference) | https://docs.wise.com/api-reference/transfer | docs.wise.com | official doc | accessed 2026-10-03 | "usually needs to be funded within fourteen days. Otherwise, it will be automatically cancelled"; cancel only from `incoming_payment_waiting` |
| S10 | Tracking transfers | https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses | docs.wise.com | official doc | 2026-09-04 | `cancelled` = "the transfer was never funded and therefore never processed" |
| S11 | Sandbox & Production Environments | https://docs.wise.com/guides/developer/environments | docs.wise.com | official doc | 2026-09-04 | Sandbox can "Initiate the fund of a transfer with balance or bulk settlement"; stable business region is "UK (Sole Trader)"; 2FA code is always `111111` |
| S12 | Simulate a balance top-up | https://docs.wise.com/api-reference/simulation/simulationbalancetopup | docs.wise.com | official doc | accessed 2026-10-03 | How to add fake money; currency "Must be the same currency as the balance account" |
| S13 | Convert from balance to balance | https://docs.wise.com/guides/product/accounts/convert-from-balance-to-balance | docs.wise.com | official doc | 2026-09-04 | Converting between your own balances is a separate quote + execute step |
| S14 | Convert or Move Money Between Balances | https://docs.wise.com/api-reference/balance/balancemovement | docs.wise.com | official doc | accessed 2026-10-03 | `POST /profiles/{profileId}/balance-movements`; lists `PersonalToken` in security |
| S15 | Retrieve bank transfer deposit details | https://docs.wise.com/api-reference/payin-deposit-detail/payindepositdetailget | docs.wise.com | official doc | accessed 2026-10-03 | Bank-transfer (push) funding: API only returns Wise's bank details; security `UserToken` only |
| S16 | teamSolutionAnalysts/wise-payment-gateway, `wiseUtil.ts` | https://github.com/teamSolutionAnalysts/wise-payment-gateway/blob/master/src/modules/wise/wiseUtil.ts | github.com | community GitHub | last commit 2022-10-07, 3 stars | Real code that funds with `type: BALANCE`. **Outdated:** legacy `/v3/.../payments` and `/v1` paths |
| S17 | foss-fund/wise-banking-api-client, `transfer.py` | https://github.com/foss-fund/wise-banking-api-client/blob/main/wise_banking_api_client/transfer.py | github.com | community GitHub | last commit 2025-01-30, 0 stars | Wraps the funding call in SCA handling. **Outdated:** host `api.sandbox.transferwise.tech`, legacy `/v3` path |
| S18 | transferwise/public-api-postman-collection | https://github.com/transferwise/public-api-postman-collection | github.com | official GitHub | last commit 2024-07-24, 47 stars | Wise's own old collection funds with `/v3/profiles/.../transfers/.../payments`. **Outdated:** uses `api.sandbox.transferwise.tech` and legacy paths |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**

Already checked **without a token** on 3 October 2026: `POST https://api.wise-sandbox.com/2026Q4/profiles/1/transfers/1/payments` returns `401` `missing_token`. So the path exists; it just needs your token.

All paths go after `{{base_url}}/{{api_version}}` (= `https://api.wise-sandbox.com/2026Q4`). Header: `Authorization: Bearer <your-token>`.

0. Write down your sandbox business profile's country and type (for example "UK, Sole Trader").
1. `GET /profiles/{profileId}/balances?types=STANDARD`. Paste each balance's `id`, `currency` and amount.
2. Create a GBP → EUR transfer (Step 0.6 rows 5–9) for **more** money than your GBP balance holds. Paste the transfer `id` and `status`.
3. **Too little money:** `POST /profiles/{profileId}/transfers/{transferId}/payments` with body `{"type": "BALANCE"}`. Paste the HTTP status code, the full body, and these headers if present: `X-2FA-Approval`, `X-2FA-Approval-Result`, `x-trace-id`.
4. `GET /transfers/{transferId}`. Paste `status`.
5. Top up GBP: `POST /simulation/balance/topup` with `{"profileId": <profileId>, "balanceId": <GBP balanceId>, "currency": "GBP", "amount": 1000}` [S12] (details in note 007). Paste the response.
6. Repeat step 3 on the same transfer. Paste code + body.
7. At once, `GET /transfers/{transferId}`. Paste `status` (this is Experiment E5 in 02-dashboard-rnd).
8. `GET /transfers/{transferId}/payments`. Paste the body.
9. **Double funding:** repeat step 3 a third time on the now-funded transfer. Paste code + body.
10. **Other currency:** create a USD → EUR transfer while your USD balance is 0 or missing (GBP has money). Fund it with `{"type": "BALANCE"}`, then with `{"type": "BALANCE", "balanceId": <GBP balanceId>}`. Paste both.
11. If any step returns `403` with an `X-2FA-Approval` header: stop. Do not retry in a loop. Paste the headers and tell Claude.

Example from docs [S2], not from your account:
```json
{
  "type": "BALANCE",
  "status": "REJECTED",
  "errorCode": "transfer.insufficient_funds"
}
```
Example from docs [S3][S4] (HTTP `201`, "BALANCE - rejected (insufficient funds)"), not from your account:
```json
{
  "type": "BALANCE",
  "status": "REJECTED",
  "errorCode": "balance.insufficient-funds"
}
```
Example from docs [S3][S4] (HTTP `201`, "BALANCE - completed"), not from your account:
```json
{
  "type": "BALANCE",
  "status": "COMPLETED",
  "balanceTransactionId": 987654321
}
```

## Finding (in your own words)
**Q6: No.** "A transfer must be created in the currency of the balance used to fund it. We currently do not support cross-balance funding" [S1].
- In practice: the transfer's **source** currency must match the balance. A GBP → EUR transfer is paid from the GBP balance, and Wise converts inside the transfer.
- If your money sits in another currency, you must first convert between your own balances (a quote, then a balance movement) [S13][S14]. Then fund.
- The documented code for "no balance in that currency" is `balance.no-balance-for-currency` [S6]. Which code the sandbox really sends is for step 10.

**Q7: The body says `"status": "REJECTED"`, and the transfer stays in `incoming_payment_waiting`** [S2].
- The docs disagree on the error code:

| Page | `errorCode` shown |
|---|---|
| Fund-from-balance guide [S2] | `transfer.insufficient_funds` |
| API reference 2026Q4 example and enum [S3][S4]; also Legacy, 2026Q3, Preview files [S5] | `balance.insufficient-funds` |
| Funding errors guide [S6] | Both. `balance.insufficient-funds` under "Balance funding errors"; `transfer.insufficient_funds` under "Integration-specific funding errors", outside "the standard fund transfer catalogue" |

- The API reference calls its list "the complete set of error codes the API can return today" and recommends a generic "funding failed" fallback for unknown codes [S3]. `transfer.insufficient_funds` is not in that list.
- Response fields [S3]: `type` (required), `status` (`CREATED`, `COMPLETED` or `REJECTED`), `errorCode` ("Present if `status = REJECTED`"), `errorMessage` ("not localised and not safe to surface to end users. May be absent"), `balanceTransactionId`, `partnerReference`.
- HTTP code: the REJECTED example sits under the `201` response [S4]. But "A successful HTTP response does not always mean that Wise funded the transfer", and a failure can also come back as a non-success HTTP code [S6].
- **Remember: decide from the body's `status`, never from the HTTP code alone.** "Mark the transfer as funded only after the response reports `COMPLETED`" [S6].
- To recover: add money, then call the same endpoint again [S2][S3].
- `balanceId` in the body: the guide sends only `type` [S2]; the API reference shows `balanceId` as optional [S3][S4].

**Funding methods** [S1][S3][S15]:

| Method | How | Who / sandbox |
|---|---|---|
| Fund from balance | `POST /profiles/{profileId}/transfers/{transferId}/payments`, `"type": "BALANCE"` | Our method. Sandbox supported [S11] |
| Bulk settlement | Same endpoint, `"type": "TRUSTED_PRE_FUND_BULK"` | Partners only; sandbox needs a Wise configuration [S1] |
| Per-transaction trusted pre-fund | Same endpoint, `"type": "TRUSTED_PRE_FUND_TX"` | Partners by agreement [S3][S6] |
| Direct bank transfer (push) | No funding call. You pay Wise's bank with reference `T<transferId>`. `GET /profiles/{profileId}/transfers/{transferId}/deposit-details/bank-transfer` gives the bank details | Lists `UserToken` only [S15] |
| Direct debit (pull) | Docs on request | "Only available to select partners" [S1]; not for USD in sandbox [S11] |

**Personal token and country.** API funding (and balance statements) work only for business accounts based in **US, Canada, Australia, New Zealand, Singapore and Malaysia** [S7][S8]. Same list as the roadmap. Wise adds that this "might change in the future" [S8]. Other accounts create the transfer by API and fund it by logging in to Wise [S8].
- **No page says whether this rule is enforced in the sandbox** [S7][S8][S11]. Only step 3 can tell.
- The sandbox's stable business region is "UK (Sole Trader)" [S11], which is not on the list.
- SCA may also block you: the fund endpoint "is SCA protected when it applies. If your profile is registered within the UK and/or EEA, SCA most likely applies" [S3]. Funding can return `403` with `X-2FA-Approval` headers [S6]. The API file says personal tokens have "(PSD2 restrictions apply for EU/UK users)" [S4]. In the sandbox the 2FA code is always `111111` [S11].

**Auto-cancel: 14 days.** "A transfer usually needs to be funded within fourteen days. Otherwise, it will be automatically cancelled" [S9]. The status becomes `cancelled` ("never funded") [S10]. Note the word "usually". You can also cancel by hand with `PUT /transfers/{transferId}/cancel`, only from `incoming_payment_waiting` [S9].

**Community code** funds the same way (`type: BALANCE`) but on legacy `/v3` paths and old hosts [S16][S17][S18]. One client adds SCA handling to the funding call [S17], so SCA is a real-world issue.

Roadmap correction: 02-dashboard-rnd.md F3 says a low balance returns `transfer.insufficient_funds`. That matches the guide [S2], but the API reference shows `balance.insufficient-funds` and does not list `transfer.insufficient_funds` at all [S3][S4][S5]. Treat both as "not enough money" until step 3 shows the real one.

Roadmap correction: Key fact 5 and Step 0.3 say "UK" is the most stable sandbox region. For business profiles the docs say "UK (Sole Trader)" [S11].

Roadmap correction (small): Key fact 7 says unfunded transfers are cancelled after 14 days. The docs say "usually" within fourteen days [S9].

## Decision (what you will do and why)
1. **Fund only from the balance in the transfer's source currency** (GBP for the GBP → EUR route). Why: cross-balance funding is not supported [S1].
2. **Mark a transfer "funded" only when the body says `COMPLETED`.** Why: the HTTP code alone can mislead [S6].
3. **Map `balance.insufficient-funds` and `transfer.insufficient_funds` to one message:** "Not enough money in your GBP balance", with "Top up and retry". Any other code: a generic "Funding failed" message. Why: the docs disagree, and Wise recommends a generic fallback [S3].
4. **Never show `errorMessage` to the user.** Save it, with `errorCode`, in the API log only. Why: "not safe to surface to end users" [S3].
5. **After a rejection, keep the same transfer and retry the same funding call.** Do not create a new transfer. Why: it stays in `incoming_payment_waiting` [S2].
6. **After a timeout or double click, check before you retry:** `GET /transfers/{transferId}` and `GET /transfers/{transferId}/payments`. Why: a second attempt can return `transfer.invalid-state` or `payment.exists` (`409`) [S3][S6].
7. **Store every funding attempt** (time, `status`, `errorCode`). Why: it fills the "Funding result" row in 02-dashboard-rnd 6.5 and helps debugging.
8. **Proposed — confirm after the experiment:** keep the UK sandbox business profile and try API funding first. If it is refused (country rule or SCA), fund in the sandbox web UI and continue with the simulation API. Why: matches the 02-dashboard-rnd E2 fallback; Wise says web funding is the normal path for most countries [S8].
9. **No balance-to-balance conversion in the MVP.** Why: one fixed route needs one currency; conversion is a separate flow [S13].

## Open questions
- Which insufficient-funds code and HTTP status does the sandbox really return (step 3)?
- Is the six-country rule enforced in the sandbox? If yes, what does the refusal look like (HTTP code, `errorCode`)?
- Will a UK sandbox business profile get an SCA `403` when funding with a personal token?
- What does the funding status `CREATED` mean? The docs list it but do not explain it [S3].
- If `balanceId` is left out, which balance does Wise use? Not documented.
- When is "usually fourteen days" not fourteen days? Calendar or business days? Not stated [S9].
- Does `balance-movements` work with a personal token? The API reference lists `PersonalToken` [S14], but the token page's list of allowed actions does not include it [S7].
