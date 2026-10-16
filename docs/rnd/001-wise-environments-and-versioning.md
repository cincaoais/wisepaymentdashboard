# 001 – Wise environments and API versioning
Date: 3 October 2026
Roadmap step: Step 0.5, Q1 (also Step 0.4, reading items 1 and 2)

## Question
- What are the sandbox and production base URLs?
- What does `2026Q4` in the path mean, and what happens on 1 January 2027?
- Extra: legacy paths (`/v1`, `/v2`, `/v3`) or versioned paths: which one should this project use? How does Wise retire a version? Why do old tutorials and old hosts break (Sandbox V2 migration)?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Sandbox & Production Environments | https://docs.wise.com/guides/developer/environments | docs.wise.com | official doc | 2026-09-04 | Base URLs (TLS and mTLS) for both environments, sandbox UI URL, sandbox does not support deprecated APIs or versions |
| S2 | Migrating to the new Sandbox | https://docs.wise.com/guides/developer/environments/sandbox-v2-migration | docs.wise.com | official doc | 2026-09-04 | Old (V1) and new (V2) hosts, key dates, what does not carry over |
| S3 | Versioning | https://docs.wise.com/guides/developer/global-versioning | docs.wise.com | official doc | 2026-10-01 | Calendar versions, the four version types, quarterly cadence, sunset and notice policy |
| S4 | Changelog | https://docs.wise.com/changelog | docs.wise.com | official doc | 2026-09-29 | 2026Q3 released July 2026 (first calendar version, opt-in), 2026Q4 released October 2026, deprecated endpoints left out of calendar versions |
| S5 | API reference (Latest) | https://docs.wise.com/api-reference | docs.wise.com | official doc | accessed 2026-10-03 | Page says `Version: 2026Q4`; servers `https://api.wise-sandbox.com/2026Q4` and `https://api.wise.com/2026Q4` |
| S6 | API reference (Preview) | https://docs.wise.com/api-reference/preview | docs.wise.com | official doc | accessed 2026-10-03 | The Preview version today is `2027Q1` |
| S7 | API reference (Legacy) | https://docs.wise.com/api-reference/legacy | docs.wise.com | official doc | accessed 2026-10-03 | Legacy servers have no version in the base URL; each path carries its own `/vN` |
| S8 | OpenAPI file, Legacy | https://docs.wise.com/_bundle/api-reference/@legacy/index.yaml | docs.wise.com | official doc | accessed 2026-10-03 | Legacy path for each endpoint in our flow (table in Finding) |
| S9 | OpenAPI file, 2026Q4 | https://docs.wise.com/_bundle/api-reference/@latest/index.yaml | docs.wise.com | official doc | accessed 2026-10-03 | Same endpoints under `/2026Q4`, with no per-endpoint number |
| S10 | Getting started with Wise API | https://docs.wise.com/guides/developer | docs.wise.com | official doc | 2026-09-16 | Base URLs again; personal-token accounts have no Developer Hub (where mTLS certificates are managed) |
| S11 | Live check: new sandbox host, no token | https://api.wise-sandbox.com/2026Q4/profiles | api.wise-sandbox.com | live check (curl, no token) | 2026-10-03 | Returns `401` `missing_token`, so the host and the `/2026Q4` path exist. `/2026Q3`, `/2027Q1` and legacy `/v2/profiles` also return `401`; `/2099Q1/profiles` returns `404` |
| S12 | Live check: old sandbox host, no token | https://api.sandbox.transferwise.tech/v2/profiles | api.sandbox.transferwise.tech | live check (curl, no token) | 2026-10-03 | Returns `410` and "This sandbox environment is no longer available". `api.sandbox.wise.tech` and `sandbox.wise.tech` give "Could not resolve host" |
| S13 | transferwise/api-docs, `_payouts.md` | https://raw.githubusercontent.com/transferwise/api-docs/master/source/includes/_payouts.md | github.com | official GitHub | archived 2020-11-19 | **Outdated:** uses `api.sandbox.transferwise.tech` and `/v1` paths. Shows what old tutorials look like |
| S14 | LarsArtmann/wise-go | https://github.com/LarsArtmann/wise-go | github.com | community GitHub | last commit 2026-10-01, 1 star | Uses the new host `api.wise-sandbox.com`, but mostly legacy `/v1`–`/v4` paths plus a few `/2026Q3` paths |
| S15 | gwillem/wise-go, `client.go` | https://raw.githubusercontent.com/gwillem/wise-go/main/client.go | github.com | community GitHub | v0.0.2 published 2026-01-18 (pkg.go.dev), 0 stars | **Outdated:** hard-codes `https://api.sandbox.transferwise.tech`, which now returns `410` |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**

Already checked **without a token** on 3 October 2026 (safe, no secret sent) [S11][S12]:

| Request | Result |
|---|---|
| `GET https://api.wise-sandbox.com/2026Q4/profiles` | `401` `{"error":"missing_token","error_description":"Missing token"}` |
| `GET https://api.wise-sandbox.com/v2/profiles` (legacy) | `401` `missing_token` |
| `GET https://api.wise-sandbox.com/2099Q1/profiles` (fake version) | `404` `{"status":"404","message":"Resource not found","error":"Not Found"}` |
| `GET https://api.sandbox.transferwise.tech/v2/profiles` (old host) | `410` "This sandbox environment is no longer available, see …sandbox-v2-migration" |

Your checklist (Postman, environment `Wise Sandbox`, header `Authorization: Bearer <your-token>`):
1. `GET {{base_url}}/2026Q4/profiles`. Paste the HTTP status and, for each profile, only `id` and `type`.
2. `GET {{base_url}}/v2/profiles` (legacy path). Paste the status. Are the profiles and field names the same as in step 1? Write down any difference.
3. `GET {{base_url}}/2026Q3/profiles` (Active version). Paste the status.
4. `GET {{base_url}}/2027Q1/profiles` (Preview). Paste the status only. Do not build on Preview.
5. From step 1, paste the response **header names** (not values). Is there a header that names the version? The docs do not mention one.
6. **Do not** send your token to any old host (`*.transferwise.tech`, `*.wise.tech`). The no-token check above is enough.

Example from docs [S5], not from your account:
```text
Sandbox Environment
https://api.wise-sandbox.com/2026Q4
```

## Finding (in your own words)
**Base URLs** [S1][S10]

| | Normal (TLS) – use this | mTLS (partners only) |
|---|---|---|
| Sandbox API | `https://api.wise-sandbox.com` | `https://api-mtls.wise-sandbox.com` |
| Sandbox web UI | `https://wise-sandbox.com` | – |
| Production API | `https://api.wise.com` | `https://api-mtls.transferwise.com` |

- mTLS needs certificates, which partners manage in Developer Hub. Personal-token accounts have no Developer Hub [S10]. So we use the TLS hosts.
- `api-mtls.transferwise.com` is a **current** production host [S1]. The retired names end in `.tech`, not `.com`.

**What `2026Q4` means**
- Wise uses calendar versions: year + quarter. One version covers the whole API, not one endpoint [S3].
- The version goes in the path, right after the host: `https://api.wise-sandbox.com/2026Q4/profiles` [S3][S5].
- Version types today:

| Type | Meaning | Today |
|---|---|---|
| Latest | Newest released version [S3] | `2026Q4` [S3][S5] |
| Active | Older released versions, still supported [S3] | `2026Q3` [S3] |
| Preview | Next quarter's version; may change without notice; use with caution [S3] | `2027Q1` [S6] |
| Legacy | Old per-endpoint versions (`/v1`…`/v4`); still supported [S3] | [S7] |

- History: `2026Q3` was the first calendar version (July 2026, opt-in). `2026Q4` came out in October 2026 [S4].

**What happens on 1 January 2027**
- Rule: each quarter, Preview becomes Latest and the old Latest becomes Active [S3]. The docs give 1 October 2026 as their example. By the same rule, on 1 January 2027 `2027Q1` becomes Latest and `2026Q4` becomes Active. (This date is worked out from the rule; the docs do not state it.)
- **Our `2026Q4` URLs keep working on 1 January 2027. Nothing breaks that day.** Active versions stay supported until Wise decides to sunset them [S3].
- Retiring a version: no fixed time frame, and "no plans right now to sunset any currently supported versions". Before a sunset, Wise gives at least **6 months'** notice by email to partner contacts and in the changelog [S3]. We are not a partner, so the changelog is our only channel.
- Inside Latest, Wise may add fields or endpoints at any time without a new version. Breaking changes go into Preview, except for security or compliance fixes [S3]. So our code must ignore fields it does not know.
- This versioning does not cover webhooks or sensitive card-details endpoints [S3].

**Legacy paths vs versioned paths for our flow** [S8][S9]

| Step | Legacy path | 2026Q4 path |
|---|---|---|
| List profiles | `GET /v2/profiles` | `GET /2026Q4/profiles` |
| List balances | `GET /v4/profiles/{profileId}/balances` | `GET /2026Q4/profiles/{profileId}/balances` |
| Create quote | `POST /v3/profiles/{profileId}/quotes` | `POST /2026Q4/profiles/{profileId}/quotes` |
| Create recipient | `POST /v1/accounts` | `POST /2026Q4/accounts` |
| Create transfer | `POST /v1/transfers` | `POST /2026Q4/transfers` |
| Fund transfer | `POST /v3/profiles/{profileId}/transfers/{transferId}/payments` | `POST /2026Q4/profiles/{profileId}/transfers/{transferId}/payments` |
| Simulate status | `GET /v1/simulation/transfers/{transferId}/{status}` | `GET /2026Q4/simulation/transfers/{transferId}/{status}` |
| Balance top-up | `POST /v1/simulation/balance/topup` | `POST /2026Q4/simulation/balance/topup` |

- Legacy: every endpoint has its own number, so you must remember four different ones. They still work [S3][S11].
- Some endpoints that were already deprecated are **not** in the calendar versions [S4]. The sandbox does not support deprecated APIs or versions [S1].
- Community code mixes both styles. One active SDK uses the new host but mostly legacy paths [S14].

**Sandbox V2 migration (why old tutorials break)** [S2]
- Old sandbox (V1): `sandbox.transferwise.tech`, `sandbox.wise.tech`, and the API hosts `api.sandbox.transferwise.tech`, `api.sandbox.wise.tech`. New sandbox (V2): `wise-sandbox.com`, `api.wise-sandbox.com`.
- Why: V2 is closer to production and more stable.
- Dates: V1 data cut-off was 1 April 2025. V1 support stopped on 30 June 2026, and Wise said it would "deprecate the environment shortly after".
- Tokens, credentials and test data made in V1 after 1 April 2025 do not work in V2. The endpoints themselves are the same; only the configuration changes.
- Today the old API host answers `410 Gone`, and the `.wise.tech` names do not resolve at all [S12].
- So an old tutorial fails because of its host, its sign-up link and its token, even if its path is still valid. Even 2026 code can be stale: one SDK published in January 2026 still points to the dead host [S15]. Old official docs also used the old host and `/v1` paths [S13].

Roadmap check: section 2, facts 2 and 3, match the live docs. No contradictions. Two additions: the old **API** hosts (`api.sandbox.transferwise.tech`, `api.sandbox.wise.tech`) are retired too [S2][S12]. Also, 30 June 2026 was the end of support; Wise said the environment itself would go "shortly after" [S2].

## Decision (what you will do and why)
1. **Base URL `https://api.wise-sandbox.com` and version `2026Q4`, kept as two separate settings** (Postman variables now, `.env` later). Reason: changing the environment or the version should mean changing one value.
2. **Use only versioned paths (`/2026Q4/...`). Never mix in legacy paths.** Reason: one rule for every endpoint, it matches the current API reference [S5], and deprecated endpoints are not in it [S4].
3. When a tutorial shows a `/v1/...` path, find that operation in the 2026Q4 reference. Never copy a host from a tutorial. Reason: hosts from before 2026 are dead [S12].
4. Stay on `2026Q4` after 1 January 2027. Read the changelog at the start of each quarter. Upgrade on purpose, one version at a time, after testing in the sandbox. Reason: Active versions keep working, and we get no email [S3].
5. The client must ignore unknown JSON fields. Reason: Wise adds fields inside Latest without notice [S3].
6. Do not use Preview (`2027Q1`). Reason: it can change without notice [S3].
7. Use the TLS hosts, not mTLS. Reason: mTLS is for partners with Developer Hub [S10].
8. Proposed — confirm after the experiment: legacy `/v2/profiles` and `/2026Q4/profiles` return the same data for our account. If they differ, record the differences here.

## Open questions
- The 1 January 2027 switch is worked out from the quarterly rule, not from a dated statement. Check the changelog in January.
- Does any response header tell you which version answered? The docs do not say (experiment step 5).
- Does `/2026Q4/profiles` return the same fields as legacy `/v2/profiles` for our account? Only the experiment can show this.
- Wise only promises sunset notice to partner contacts and in the changelog. It is not known whether personal-token users get any email.
