# 011 – Webhooks vs polling
Date: 3 October 2026
Roadmap step: Step 0.5, Q13 (also Phase 5.1 polling, Phase 5.2 webhooks, experiment E3 in 02-dashboard-rnd)

## Question
Webhooks vs polling: what does each need from your setup (a public URL? HTTPS?), and which is easier to start with?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Webhooks and notifications | https://docs.wise.com/guides/developer/webhooks | docs.wise.com | official doc | 2026-09-21 (last updated) | Two subscription levels; URL rules; retry policy; sandbox IPs |
| S2 | Subscribe to webhooks | https://docs.wise.com/guides/developer/webhooks/subscribe-to-webhooks | docs.wise.com | official doc | 2026-09-04 (last updated) | Request body; Developer Hub is application-level and needs permission |
| S3 | Event handling | https://docs.wise.com/guides/developer/webhooks/event-handling | docs.wise.com | official doc | 2026-09-04 (last updated) | 2xx within 5 s; 25 retries over two weeks; signature; both public keys |
| S4 | Event ordering | https://docs.wise.com/guides/developer/webhooks/event-ordering | docs.wise.com | official doc | 2026-09-17 (last updated) | No order guarantee; use `data.occurred_at`; schema 4.0.0 |
| S5 | Transfer state change event | https://docs.wise.com/api-reference/webhook-event/eventtransfersstatechange | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Profile level "Supported"; payload; `X-Delivery-Id` is per "delivery attempt" |
| S6 | Create profile webhook subscription | https://docs.wise.com/api-reference/webhook/webhookprofilesubscriptioncreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `POST /profiles/{profileId}/subscriptions`; security lists only `UserToken` |
| S7 | Create application webhook subscription | https://docs.wise.com/api-reference/webhook/webhookapplicationsubscriptioncreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | Needs `clientKey` from Wise tech support + client-credentials token |
| S8 | Webhook subscription errors | https://docs.wise.com/guides/developer/errors/webhooks | docs.wise.com | official doc | 2026-09-22 (last updated) | `INVALID_CALLBACK_URL` includes an "accessibility" check |
| S9 | View and retry events | https://docs.wise.com/guides/developer/webhooks/view-retry-events | docs.wise.com | official doc | 2026-09-04 (last updated) | A manual retry creates a new delivery ID |
| S10 | Migrating to the new Sandbox | https://docs.wise.com/guides/developer/environments/sandbox-v2-migration | docs.wise.com | official doc | 2026-09-04 (last updated) | "The public keys listed in API Docs work for V1 and V2" |
| S11 | Environments | https://docs.wise.com/guides/developer/environments | docs.wise.com | official doc | 2026-09-04 (last updated) | Sandbox supports transfer state-change webhooks |
| S12 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 (last updated) | What a personal token may do (subscriptions not named) |
| S13 | Get a transfer by ID | https://docs.wise.com/api-reference/transfer/transferget | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `GET /transfers/{transferId}`; allows `PersonalToken` |
| S14 | List transfers | https://docs.wise.com/api-reference/standard-transfer/transferlist | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `GET /transfers?profile=&status=`; allows `PersonalToken` |
| S15 | Tracking transfers | https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses | docs.wise.com | official doc | 2026-09-04 (last updated) | Final statuses; bounce-backs up to "several weeks" later |
| S16 | Getting started (Rate limiting) | https://docs.wise.com/guides/developer | docs.wise.com | official doc | 2026-09-16 (last updated) | Personal token: 100 req/s, 900 req/min per user |
| S17 | transferwise/digital-signatures-examples – verify-webhook-signature | https://github.com/transferwise/digital-signatures-examples/tree/main/verify-webhook-signature | github.com | official GitHub, **partly outdated**: README links the old `api-docs.wise.com`; sample uses schema 2.0.0 | last commit 2021-09-16; 15 stars | Java/Node/Ruby verification; PKCS#1 v1.5 + SHA-256; sandbox key = current docs key |
| S18 | pywisetransfer `webhooks.py` | https://github.com/jayaddison/pywisetransfer/blob/main/pywisetransfer/webhooks.py | github.com | community GitHub, **outdated**: `api.sandbox.transferwise.tech`, `/v3/profiles/{id}/subscriptions`; archived 2026-08-31 | last commit 2026-08-21; 16 stars | Python verification with `cryptography`, `PKCS1v15()` + `SHA256()` |
| S19 | ngrok – Test Webhooks Locally | https://ngrok.com/docs/share-localhost/webhooks | ngrok.com | official doc (tool) | accessed 2026-10-03 | `ngrok http <port>` gives a public HTTPS URL; inspect and replay requests |
| S20 | ngrok – Free Plan Limits | https://ngrok.com/docs/pricing-limits/free-plan-limits | ngrok.com | official doc (tool) | accessed 2026-10-03 | Free plan: one fixed dev domain, HTTPS, 20,000 requests/month |
| S21 | Cloudflare – Quick Tunnels | https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/ | cloudflare.com | official doc (tool) | last updated 2026-09-30 | No account; hostname changes every time; testing only |
| S22 | Django – Cross Site Request Forgery protection | https://docs.djangoproject.com/en/stable/ref/csrf/ | djangoproject.com | official doc | accessed 2026-10-03 (Django 6.1) | POSTs without a CSRF token get 403; `csrf_exempt` |
| S23 | Django – Request and response objects | https://docs.djangoproject.com/en/stable/ref/request-response/ | djangoproject.com | official doc | accessed 2026-10-03 (Django 6.1) | `HttpRequest.body` = "The raw HTTP request body as a bytestring" |
| S24 | cryptography – RSA | https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/ | cryptography.io | official doc | accessed 2026-10-03 | `verify()`; PSS and PKCS1v15 are both valid paddings |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**
Part A – polling (do this in Phase 0):
1. `GET /transfers/{{transfer_id}}` [S13]. Paste `status`.
2. Run the `processing` simulation, wait 5 s, repeat step 1. Paste old status, new status, and the time between.
3. `GET /transfers?profile={{profile_id}}&status=incoming_payment_waiting,processing,funds_converted&limit=10&offset=0` [S14]. Is the response a JSON array? Which IDs?
4. Look at the response headers of a normal 200. Any rate-limit headers? ([S16] only describes 429.)

Part B – webhooks (stretch goal = experiment E3):
5. `GET /profiles/{{profile_id}}/subscriptions`. Paste status and body. A 401 or 403 probably means your token type is not allowed (read the body).
6. Start `ngrok http 8000` [S19]. Copy the HTTPS URL.
7. `POST /profiles/{{profile_id}}/subscriptions` with the body from [S2]: `name`, `trigger_on: "transfers#state-change"`, `delivery.version: "4.0.0"`, `delivery.url: <ngrok URL>/wise/webhook`. Paste status and body. If 401/403: stop and record "personal token cannot subscribe".
8. If it worked: open ngrok's Traffic Inspector [S19]. Did a test event arrive (`X-Test-Notification: true`)? Run a simulation and paste the headers (`X-Signature-SHA256`, `X-Delivery-Id`) and body. Your app is not ready yet, so Wise will see an error and retry. That is fine.
9. Clean up: `DELETE /profiles/{{profile_id}}/subscriptions/{{subscription_id}}`.

Example from docs [S4], not from your account:
```json
{ "data": { "resource": { "type": "transfer", "id": 111 },
    "current_state": "processing", "previous_state": "incoming_payment_waiting",
    "occurred_at": "2024-06-15T10:30:00.123Z" },
  "subscription_id": "01234567-89ab-cdef-0123-456789abcdef",
  "event_type": "transfers#state-change", "schema_version": "4.0.0",
  "sent_at": "2024-06-15T10:30:01.456Z" }
```

## Finding (in your own words)
**Direct answer. Polling needs only your token. Webhooks need a public HTTPS URL, a subscription, and signature checks. Polling is easier to start with.**

| Needs | Polling | Webhooks |
|---|---|---|
| Public URL | No | Yes. A real domain name; IP addresses are not allowed [S1] |
| HTTPS | Only for your calls to Wise | Port 443, certificate from a trusted CA, no query string, no redirects [S1] |
| Setup at Wise | None | A subscription [S2][S6] |
| Security work | None extra | Verify the RSA signature [S3] |
| Works with a personal token? | Yes: both endpoints allow `PersonalToken` [S13][S14] | Not documented (see below) |

**Two subscription levels** [S1][S2]
- Application-level: events for resources your application created. Wise says "In most cases, you should subscribe to the application-level webhook" [S1]. It needs a `clientKey` from Wise tech support and a client-credentials token [S7]. Developer Hub webhooks are application-level only and need access permission [S2]. **This is partner access. We do not have it.**
- Profile-level: `POST /profiles/{profileId}/subscriptions` with a user token [S2][S6]. `transfers#state-change` supports it [S5].
- Personal token? [S12] lists quotes, recipients, transfers, batch groups and "tracking transfer events", but not subscriptions. [S6] lists only `UserToken`. The docs do not settle it. Step 7 will.
- Wise checks your URL when you subscribe ("accessibility") [S8]. So the tunnel must already be running.

**Delivery rules**
- Reply 2xx within 5 seconds or the attempt fails [S3]. [S1] says success means "a 200 response". Reply exactly 200.
- Retries: 1 min, then doubling up to 24 h; after the 11th retry, 14 more once a day [S1]. "up to 25 times ... over a two week period" [S3]. Delivery is "best-effort" [S1].
- For 400, 401, 403, 404, 405, 409, 410, 417, 422 Wise tries only three times [S1]. Django's CSRF check answers 403 to a POST without a token [S22]. **So the webhook view must be `csrf_exempt`, or Wise gives up after three tries.**
- Order is not guaranteed. For `transfers#state-change` use `data.occurred_at`. Subscribe with schema `4.0.0` for millisecond timestamps [S4][S5].
- Store first, process later: "do some basic validation and then store the notification for processing by a separate server process" [S3].

**Signature**
- Header `X-Signature-SHA256`, Base64. RSA with a SHA-256 digest of the message body [S3].
- Wise's examples use PKCS#1 v1.5 padding (Node: `RSA_PKCS1_PADDING`) [S17]. The `cryptography` docs show PSS in their example, but PKCS1v15 is also valid [S24]. A Python client uses `PKCS1v15()` + `SHA256()` [S18].
- Verify the raw bytes, not re-encoded JSON. In Django that is `request.body` [S23].
- **Sandbox and production use different public keys.** Both are printed on [S3]. The migration guide says the public keys "work for V1 and V2" (in its "mTLS for Webhooks" part) [S10]. The sandbox key in [S17] and [S18] is identical to [S3] (checked 3 Oct 2026).

**Laptop development**
- Wise's webhook docs do not mention ngrok or any tunnel [S1][S2][S3].
- ngrok: `ngrok http <port>` gives a public HTTPS URL. Its Traffic Inspector shows headers and body and can replay a request [S19]. Free plan: one fixed dev domain (`*.ngrok-free.app`), HTTPS included [S20].
- Cloudflare Quick Tunnel: `cloudflared tunnel --url http://localhost:8080`, no account. The hostname changes every time [S21], so you would re-subscribe at Wise after every restart.

**Polling design**
- One transfer: `GET /transfers/{transferId}` [S13]. Many: `GET /transfers?profile=…&status=a,b,c&limit=…&offset=…` [S14].
- I found no recommended polling interval in Wise's docs. Limit for a personal token: 100 requests/second, 900/minute per user [S16].
- `outgoing_payment_sent` is final only "assuming funds will not be returned". Bounce-backs are mostly 2–3 business days, but can come "several weeks" later [S15].
- In the sandbox, status only changes when you simulate it. So "refresh after simulate" shows everything.

Roadmap correction: Phase 5.2 says "`X-Delivery-Id` is unique per delivery. Use it to ignore duplicates." [S5] calls it unique per "delivery attempt", a manual retry gets a new delivery ID [S9], and two subscriptions send two callbacks [S1]. Deduplicate on transfer `id` + `current_state` + `occurred_at`. Keep `X-Delivery-Id` for the log.
Roadmap note (refinement, not a contradiction): Phase 5.1 refreshes "every transfer that isn't in a final status". Also re-check `outgoing_payment_sent` now and then, because of late bounce-backs [S15].
Confirmed: HTTPS on 443 with a real domain [S1]; 5-second reply [S3]; sandbox key from the event-handling page [S3]; out-of-order events and `occurred_at` [S4]; Developer Hub needs partner access [S2].

## Decision (what you will do and why)
1. **Polling first, webhooks as a stretch goal** (same as the roadmap). Why: polling works with a personal token [S13][S14], needs no public URL, and in the sandbox you trigger every change yourself.
2. "Refresh status" button → `GET /transfers/{transferId}`. Management command → one `GET /transfers` call filtered on non-final statuses, run by hand or every 5 minutes. *Proposed — interval is our choice; none found in Wise's docs.*
3. Re-check `outgoing_payment_sent` transfers once a day for 30 days. *Proposed — Wise says "several weeks" without a number [S15].*
4. On 429, wait for `Retry-After` (see note 009).
5. Webhooks only after step 7 succeeds. Then: ngrok with the fixed dev domain [S20], schema `4.0.0`, a `csrf_exempt` view, PKCS1v15 check on `request.body` with the key chosen by environment, store raw event, reply 200, process later, deduplicate by business key, order by `occurred_at`. Keep polling as a safety net, because delivery is best-effort [S1].
6. If step 7 fails: record it and stay with polling. Webhooks page becomes "Won't" (02-dashboard-rnd E3).

## Open questions
- Can a personal token create a profile-level subscription? (step 7)
- Does creating a profile-level subscription send a test event? [S2] says so for the API (application-level) and Developer Hub only.
- Do automatic retries keep the same `X-Delivery-Id`? Not stated.
- Do sandbox simulations trigger profile-level `transfers#state-change` events? [S11] says the sandbox supports these webhooks, not which level.
- Which rate-limit row ("Android and Web" or "iOS") applies to a server app [S16]?
