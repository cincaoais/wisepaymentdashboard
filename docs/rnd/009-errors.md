# 009 – Wise error responses and how the app reacts
Date: 3 October 2026
Roadmap step: Step 0.5, Q11 (also Step 0.6 part 3 "Break it on purpose", Step 3.1 client design)

## Question
What does a Wise error response look like? How should your app react to 401 vs 422 vs 500?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Handle API errors | https://docs.wise.com/guides/developer/errors | docs.wise.com | official doc | 2026-09-22 (last updated) | Status-code table; retry rules; `x-trace-id`; 429 and `Retry-After` |
| S2 | Authentication and access errors | https://docs.wise.com/guides/developer/errors/authentication | docs.wise.com | official doc | 2026-09-22 (last updated) | `invalid_token` body; 401 vs 403; SCA headers |
| S3 | Recipient errors | https://docs.wise.com/guides/developer/errors/recipients | docs.wise.com | official doc | 2026-09-22 (last updated) | `errors[]` with `path`; 400 or 422; no blind retry of recipient create |
| S4 | Quote errors | https://docs.wise.com/guides/developer/errors/quotes | docs.wise.com | official doc | 2026-09-22 (last updated) | Expired quote = 422; 401 for valid token without profile access; problem-style 400 body |
| S5 | Transfer errors | https://docs.wise.com/guides/developer/errors/transfers | docs.wise.com | official doc; example is labelled with a legacy path (`POST /v1/transfers`) | 2026-09-22 (last updated) | Reuse `customerTransactionId` on retry |
| S6 | Funding errors | https://docs.wise.com/guides/developer/errors/funding | docs.wise.com | official doc | 2026-09-22 (last updated) | Business failure inside a 2xx success response (`status: REJECTED`); `payment.exists` |
| S7 | Webhook subscription errors | https://docs.wise.com/guides/developer/errors/webhooks | docs.wise.com | official doc | 2026-09-22 (last updated) | Single-object error shape; "support both" shapes |
| S8 | Create a transfer | https://docs.wise.com/api-reference/standard-transfer/transfercreate | docs.wise.com | official doc | accessed 2026-10-03 (API version 2026Q4) | Retrying with the same `customerTransactionId` does not duplicate |
| S9 | Getting started with Wise API (Rate limiting, Idempotency) | https://docs.wise.com/guides/developer | docs.wise.com | official doc | 2026-09-16 (last updated) | Personal-token rate limits; which operations are idempotent |
| S10 | Correlation ID | https://docs.wise.com/guides/developer/headers/correlation-id | docs.wise.com | official doc; its example uses a legacy path (`GET /v1/transfers/123`) | 2026-09-04 (last updated) | `X-External-Correlation-Id` rules |
| S11 | Retrieve recipient account requirements (response headers) | https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `x-trace-id`, `Retry-After`, `X-Rate-Limited-By` headers |
| S12 | Changelog | https://docs.wise.com/changelog | docs.wise.com | official doc | 2026-09-29 (last updated) | April 2026: both headers, and 429 with `Retry-After`/`X-Rate-Limited-By`, documented on all operations |
| S13 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 (last updated) | Personal tokens stay active until revoked; made by hand in the web UI |
| S14 | pywisetransfer `endpoint.py` | https://github.com/jayaddison/pywisetransfer/blob/main/pywisetransfer/endpoint.py | github.com | community GitHub, **outdated**: uses `api.sandbox.transferwise.tech` and `/v3` paths; archived 2026-08-31 | last commit 2026-08-21; 16 stars | A real client reads `code`/`message` on 403 and checks `X-2FA-Approval-Result` |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**
For each request paste: HTTP status, the full JSON body, and the headers `x-trace-id`, `X-External-Correlation-Id`, `Retry-After` (if present).
1. Wrong token: `GET /profiles` with `Authorization: Bearer wrong-token`.
2. No token: `GET /profiles` with no `Authorization` header.
3. Correlation: `GET /profiles` with your token and `X-External-Correlation-Id: <a new UUID>`. Is it echoed back? Is there an `x-trace-id`? [S10][S11]
4. Bad quote ID: `GET /quotes/not-a-real-id/account-requirements`.
5. Expired quote: `PATCH /profiles/{{profile_id}}/quotes/{{quote_id}}` on a quote older than 30 minutes [S4].
6. Bad IBAN: `POST /accounts` with IBAN `DE00` (same as note 008 step 8).
7. Broken JSON: `POST /accounts` with body `{"currency":` (cut off). Which of the shapes below comes back?
8. Duplicate: `POST /transfers` twice with the **same** `customerTransactionId`. Is the second response the same transfer `id`? Which status code?
9. Low balance: fund a transfer bigger than your balance. Is the HTTP status a 2xx success (200 or 201?) with `"status": "REJECTED"`? Which `errorCode`?
Do **not** try to trigger a 429 on purpose.

## Finding (in your own words)
**Direct answer. There is no single error shape.** The most common is an `errors` array. Your client must read all of these:

| Shape | Example from docs, not from your account | Seen in |
|---|---|---|
| `errors` array | `{"timestamp": "2026-08-18T10:15:30Z", "errors": [{"code": "NOT_VALID", "message": "Please specify an IBAN.", "path": "IBAN", "arguments": ["IBAN"]}]}` | recipients [S3], quotes [S4], transfers [S5] |
| OAuth style | `{"error": "invalid_token", "error_description": "Invalid token"}` | auth [S2] |
| Single object | `{"code": "INVALID_CALLBACK_URL", "message": "...", "arguments": ["http://example.com/webhook"]}` | webhook subscriptions [S7] |
| Problem style | `{"detail": "Failed to convert 'quoteId' with value: 'None'", "status": 400, "title": "Bad Request", ...}` | unreadable request [S4] |
| Failure inside a 2xx success | `{"type": "BALANCE", "status": "REJECTED", "errorCode": "balance.insufficient-funds"}` | funding [S6] |

- `path` names the bad field. `code` is only unique inside one operation. Never make decisions from `message` text [S1][S3].
- Do not show `error_description` to users [S2].

| HTTP | Meaning for Wise [S1] | What our app should do | Safe to retry? |
|---|---|---|---|
| 400 / 422 | Parsing, field validation or business rule failed | Show each `errors[].path` next to its field. Expired quote (422) → make a new quote [S4] | Only after the input changes |
| 401 | Missing/invalid token, **or** a valid token that cannot access this profile [S2][S4] | Red connection card: "token invalid or no access to this profile". Check the `profileId` too | No. [S13] describes no refresh for personal tokens; you make a new one in the web UI |
| 403 | Access denied, or SCA needed (check `X-2FA-Approval`, `X-2FA-Approval-Result`) [S2] | Generic "not allowed" message. SCA is out of scope for this project | No |
| 404 | Not found, or not visible to this token/profile | Check ID, profile and environment (sandbox vs production) | No |
| 408 | Timed out; outcome may need checking | Treat as "unknown result" (see retries below) | Only after checking, or with an idempotency ID |
| 409 | Conflicts with the resource's current state | Read the resource again; show its real state | No |
| 429 | Rate limit reached | Wait at least `Retry-After`, then back off with jitter, with a limit [S1] | Yes, after waiting |
| 5xx | Wise or a downstream service failed | Show "Wise is having problems". Log `x-trace-id` | Depends on the operation (below) |

**Retries and `customerTransactionId`**
- "A timeout or connection failure does not prove that Wise rejected the request" [S1]. "A 5xx response alone does not establish a transient failure" [S1].
- **Create transfer is safe to retry only with the same `customerTransactionId`.** "Subsequent retry messages are treated as repeat messages and will not create duplicate transfers" [S8]. A new ID is a new transfer [S5].
- Other idempotent operations use a header, `X-idempotence-uuid` (balance moves) [S9]. Idempotency is per operation, not global [S9].
- Recipient create has no idempotency key in the docs. After a timeout, list recipients before you create again [S3].
- Funding: check the result body, even on a 2xx success [S6]. A second attempt can fail with `payment.exists`; then reconcile, do not pay again [S6].

**Headers that help debugging**
- `X-External-Correlation-Id` (you send it): optional, UUID recommended, max 36 characters (longer is ignored). Wise echoes it back but **does not log or store it**. No personal data in it [S10].
- `x-trace-id` (Wise sends it): "Useful when contacting support about a specific request" [S11]. Record it [S1]. Both documented on all operations since April 2026 [S12].
- On 429: `Retry-After` (seconds) and `X-Rate-Limited-By` [S11].

**Rate limits** for a business account with a personal token are per user: 100 requests/second and 900 requests/minute ("Android and Web") [S9]. Some services have extra limits, e.g. number of quotes [S9].

**Community evidence:** pywisetransfer catches 403, reads `code`/`message`, and checks `X-2FA-Approval-Result` for SCA [S14]. This matches [S2]. Its hosts are retired.

Roadmap correction: 02-dashboard-rnd F3 says low balance gives `transfer.insufficient_funds`. The funding guide lists `balance.insufficient-funds` for balance funding, and `transfer.insufficient_funds` only as an "integration-specific" code [S6]. Handle both.
Roadmap note (addition, not a contradiction): Step 3.1 and 02-dashboard-rnd Page 5 mention only the correlation ID. Wise does not store it [S10], so it helps only your own logs. Also log the `x-trace-id` from each response; that is what Wise support needs [S1][S11].
Warning (Wise's own docs): two examples use legacy `/v1/` paths [S5][S10]. In this project always use `/2026Q4/...`.

## Decision (what you will do and why)
1. One error class in the Wise client. It holds: HTTP status, a list of `(code, path, message)`, the redacted body, `x-trace-id`, and our correlation ID. It parses all five shapes. Why: [S7] says support more than one envelope.
2. Send a new UUID as `X-External-Correlation-Id` on every request. Save it and `x-trace-id` in the API activity log. Why: [S1][S10].
3. Automatic retries only for: GET requests (on timeout, 429, 5xx) and `POST /transfers` (same `customerTransactionId`). Max 3 attempts, waits about 1 s, 2 s, 4 s plus jitter, never shorter than `Retry-After`. *Proposed — numbers are our choice; the docs only say "bounded" backoff with jitter and a "sensible retry limit" [S1][S8].*
4. Never auto-retry `POST /accounts` or funding. Check state first (list recipients; `GET /transfers/{transferId}/payments` [S6]). Why: no documented idempotency [S3][S6].
5. Save `customerTransactionId` in the database **before** calling Wise. Why: a retry must reuse it [S5][S8].
6. 401 → stop and show the connection card. No token-refresh logic. Why: [S13] describes no refresh flow for personal tokens.
7. Funding: treat the transfer as funded only when the body says `COMPLETED` [S6].

## Open questions
- Exact body for a wrong token in the sandbox: `invalid_token`, `unauthorized`, or something else? (steps 1–2)
- Duplicate `customerTransactionId`: do you get the first transfer back with 200, or an error? [S8] only says "will not create duplicate transfers". (step 8)
- Bad IBAN: 400 or 422? (step 6)
- Which insufficient-funds code does the sandbox send? (step 9)
- Does Wise ever send 408, or is that only your own client timeout? Not explained.
- Which limit applies to a server app with a personal token: "Android and Web" or "iOS"? [S9] does not say.
