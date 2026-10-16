# 002 – Profiles and personal API tokens
Date: 3 October 2026
Roadmap step: Step 0.5, Q2, and Step 0.3 (sandbox account, token, country choice)

## Question
- Q2: What is a profile? Why does almost every endpoint need a `profileId`?
- Step 0.3: What can and can't a personal API token do? Where is it created? Is it shown only once? How is it sent? How do I keep it safe?
- Step 0.3: Which country should the sandbox business profile use: UK (most stable in the sandbox) or MY/SG (where a personal token may fund transfers by API)? (a) Which regions may fund by API today? (b) Does that rule also apply in the **sandbox**? (c) What does Wise tell everyone else to do? Do any endpoints need SCA or 2FA?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | About profiles | https://docs.wise.com/guides/product/account-setup/about-profiles | docs.wise.com | official doc | 2026-09-23 | What a profile is, the two types, and why Wise uses `profileId` |
| S2 | Profile (API reference) | https://docs.wise.com/api-reference/profile | docs.wise.com | official doc | accessed 2026-10-03 | "Most API endpoints require a `profileId` parameter" |
| S3 | List profiles | https://docs.wise.com/api-reference/profile/profilelist | docs.wise.com | official doc | accessed 2026-10-03 | `GET /profiles` returns a list; "there might be more than one business profile" |
| S4 | OpenAPI file, 2026Q4 | https://docs.wise.com/_bundle/api-reference/@latest/index.yaml | docs.wise.com | official doc | accessed 2026-10-03 | Profile `id` is int64; `type` is `PERSONAL` or `BUSINESS`; which endpoints list `PersonalToken`; "PSD2 restrictions apply for EU/UK users"; where the profile goes in each request |
| S5 | Getting started with Wise API | https://docs.wise.com/guides/developer | docs.wise.com | official doc | 2026-09-16 | A user holds profiles; tokens are issued for a user; personal-token accounts get no client ID/secret and no Developer Hub; rate limits |
| S6 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 | What the token can do, the six funding regions, how to create, send and revoke it, safety rules |
| S7 | Payouts for SMBs | https://docs.wise.com/guides/product/send-money/use-cases/payouts-smbs | docs.wise.com | official doc | 2026-09-04 | Same six regions; access level "full or read only"; "Log into the Wise account to fund the transfer"; profile webhooks |
| S8 | Security and access | https://docs.wise.com/guides/developer/auth-and-security | docs.wise.com | official doc | 2026-09-04 | Personal tokens are for SMBs; use separate credentials for sandbox and production |
| S9 | Strong Customer Authentication & 2FA | https://docs.wise.com/guides/developer/auth-and-security/sca-and-2fa | docs.wise.com | official doc | 2026-09-22 | SCA in the UK and EEA for funding and statements; SCA applies outside US, AU, NZ, SG, CA, MY; answer is `403` |
| S10 | Fund a transfer (API reference) | https://docs.wise.com/api-reference/transfer/transferfund | docs.wise.com | official doc | accessed 2026-10-03 | Endpoint accepts a personal token; "If your profile is registered within the UK and/or EEA, SCA most likely applies to you" |
| S11 | One Time Token | https://docs.wise.com/guides/developer/auth-and-security/one-time-token | docs.wise.com | official doc | 2026-09-04 | SCA answer: `403` with headers `x-2fa-approval-result` and `x-2fa-approval` |
| S12 | Funding errors | https://docs.wise.com/guides/developer/errors/funding | docs.wise.com | official doc | 2026-09-22 | Funding error codes; always check `status` and `errorCode`; check SCA headers on `403` |
| S13 | Sandbox & Production Environments | https://docs.wise.com/guides/developer/environments | docs.wise.com | official doc | 2026-09-04 | Most stable sandbox setup is business "UK (Sole Trader)" with GBP/USD/EUR; 2FA code is always `111111`; SCA "can be disabled via your client credentials" |
| S14 | Simulate transfer state change | https://docs.wise.com/api-reference/simulation/simulationtransferstatechange | docs.wise.com | official doc | accessed 2026-10-03 | "Fund the transfer first before calling any simulation endpoints"; page lists only `UserToken` |
| S15 | Setting up a Wise Account | https://docs.wise.com/guides/developer/account-creation | docs.wise.com | official doc | 2026-09-21 | UI sign-up order: register, personal profile, then business profile |
| S16 | Migrate to OAuth 2.0 and mTLS | https://docs.wise.com/guides/developer/auth-and-security/personal-token-migration | docs.wise.com | official doc | 2026-09-22 | Partners moving to OAuth: "personal token logic will be deprecated by the end of next year, once your migration is successful" |
| S17 | transferwise/api-docs, `_payouts.md` | https://raw.githubusercontent.com/transferwise/api-docs/master/source/includes/_payouts.md | github.com | official GitHub | archived 2020-11-19 | **Outdated:** V1 host and `/v1` paths. Said the old V1 sandbox had SCA "disabled" by default and you could switch it on |
| S18 | transferwise/digital-signatures-examples, SCA for personal tokens | https://github.com/transferwise/digital-signatures-examples/blob/main/sca-personal-tokens/README.md | github.com | official GitHub | last push 2022-07-09, 15 stars | **Outdated:** links to `api-docs.transferwise.com`. Shows the old method: sign the one-time token with your own key |
| S19 | we-promise/sure issue #3944 | https://github.com/we-promise/sure/issues/3944 | github.com | community GitHub | opened 2026-10-02 (repo 10.4k stars) | Quotes Wise's settings page: "we no longer support signing API requests to complete strong customer authentication on personal Wise accounts … You can no longer retrieve account statements or fund payments using this method." Production, personal profile in Spain |
| S20 | we-promise/sure issue #3384 | https://github.com/we-promise/sure/issues/3384 | github.com | community GitHub | 2026-09-04 | Production **business** profile got `403` on statements; uses legacy `/v1` paths |
| S21 | gwillem/wise-go README | https://github.com/gwillem/wise-go | github.com | community GitHub | v0.0.2, 2026-01-18 (pkg.go.dev), 0 stars | "EU/UK business accounts cannot fund transfers via API using personal tokens"; workaround: fund in the Wise app. **Outdated host** (`api.sandbox.transferwise.tech`) |
| S22 | Live check, no token | https://api.wise-sandbox.com/2026Q4/profiles | api.wise-sandbox.com | live check (curl, no token) | 2026-10-03 | Answer without a token: `401` `{"error":"missing_token","error_description":"Missing token"}` |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**

1. Sign up at `https://wise-sandbox.com`. Create the personal profile, then a business profile: **country UK, type Sole Trader**. Paste: a screenshot of the profile page (hide personal data), and the country and business-type options the form offered.
2. Create the token: **Your Account → Connect and manage apps → API tokens → Add new token**. If asked for a 2FA code, use `111111` [S13]. Choose **full** access. Paste: did the menu match? Which access levels were offered? Was the token shown only once? (Never paste the token.)
3. `GET {{base_url}}/{{api_version}}/profiles` with header `Authorization: Bearer <your-token>`. Paste the status and, for each profile, only `id`, `type` and `address.countryIso2Code`.
   Example from docs [S3], not from your account (shortened):
   ```json
   [ { "type": "PERSONAL", "id": 14575282, "userId": 9889627, "fullName": "Sarah Jenkins" },
     { "type": "BUSINESS", "id": 14599371, "userId": 9889627, "businessName": "Innovate Solutions Ltd", "companyType": "LIMITED_COMPANY" } ]
   ```
4. `GET {{base_url}}/{{api_version}}/profiles/{{profile_id}}` for the business profile. Paste the status.
5. Change one character of the token and repeat step 3. Paste the status and body.
6. During Step 0.6, write down the HTTP status for: create quote, create recipient (`POST /accounts`) and balance top-up simulation. Reason: the reference lists only `UserToken` for these [S4][S14], but the guide says a personal token can create quotes and recipients [S6].
7. **Funding test (E2)**, during Step 0.6 request 10: `POST {{base_url}}/{{api_version}}/profiles/{{profile_id}}/transfers/{{transfer_id}}/payments` with body `{"type": "BALANCE"}`. Paste: the HTTP status, whether `x-2fa-approval-result` and `x-2fa-approval` headers were present (yes/no only), and the full body.
   Compare with the docs (examples from docs, not from your account):
   - Success: `{"type": "BALANCE", "status": "COMPLETED", ...}` [S12]
   - SCA needed: `403` with `x-2fa-approval-result: REJECTED` [S11]
   - Documented refusal codes: `balance.unauthorised.missing-security-role`, `balance.payment-option-unavailable`, `transfer.not-accessible-for-user` [S12]
8. If step 7 is refused: fund the same transfer in the sandbox **web UI**. Then call the `processing` simulation and `GET /transfers/{transferId}`. Paste both statuses.

## Finding (in your own words)
**Profiles (Q2)**
- A profile is the legal identity that owns the money and the actions. There are two types: `PERSONAL` (a person) and `BUSINESS` (a company or sole trader) [S1][S4].
- One login (a "user") can hold several profiles [S5]. `GET /profiles` lists "all profiles belonging to user" [S4]. In the web UI you create a personal profile first, then a business one [S15]. So expect your token to see **at least two profiles** (experiment step 3 checks this). There may even be more than one business profile [S3].
- Why `profileId` is everywhere: Wise uses it to know who sends the money, to run KYC/AML checks, to keep recipients and balances private to that profile, and to apply limits [S1]. "Every transactional resource … is scoped to a specific `profileId`" [S1][S2].
- **The token says who you are; the `profileId` says which of your identities is acting.**
- Where it goes [S4]: in the path (quotes, balances, funding); in the body (`profile` in `POST /accounts`); or through the quote (`POST /transfers` has no profile field, but its `quoteUuid` belongs to a profile).
- A profile `id` is a 64-bit integer (`int64`) [S4].

**Personal API token: can and cannot**

| Can | Cannot |
|---|---|
| Create quotes, list and create recipients, create transfers and batch groups, track transfer events [S6] | Fund transfers or get balance statements by API, unless the account is based in the US, Canada, Australia, New Zealand, Singapore or Malaysia [S6][S7] |
| Track transfers through profile webhooks [S7] | Use Developer Hub, client ID/secret, or OAuth features [S5] |
| Listed in the 2026Q4 reference for: list/get profiles, list/create balances, create/get/list/cancel transfers, fund a transfer [S4][S10] | Anything beyond this needs a partnership with Wise [S6] |

- Docs mismatch: the 2026Q4 reference lists only `UserToken` for create quote, update quote, list/create recipients and the simulation endpoints [S4][S14]. The guides say a personal token can create quotes and recipients [S6][S7]. Experiment step 6 will show which is right.
- Create it in the business account: **Your Account → Connect and manage apps → API tokens → Add new token**. Complete 2-step verification. Give it a name and an access level, **full or read only** [S6][S7]. The docs describe wise.com. We assume the sandbox UI at wise-sandbox.com has the same menu (experiment step 2 checks this). The sandbox 2FA code is always `111111` [S13].
- **The token is shown only once** [S6].
- Send it on every request as `Authorization: Bearer <your-token>` [S6][S4]. Without it, the sandbox answers `401 missing_token` [S22].
- It stays active until you revoke it. Revoking works from the same page and takes effect immediately [S6].
- Safety [S6][S8]: keep it in a secrets manager, never in code or Git. Never log it or put it in a URL. Revoke and replace it if it may have leaked. Use separate tokens for separate apps, and separate credentials for sandbox and production.

**Country trade-off**
- (a) **Regions:** API funding (and statements) with a personal token is allowed only for accounts based in the **US, Canada, Australia, New Zealand, Singapore and Malaysia** [S6][S7]. The UK is not on the list. For most countries, funding by API is "not supported" [S7]. Wise warns that this list "might change in the future" [S7].
- Why: PSD2 requires SCA in the UK and EEA for funding and statements [S9]. SCA applies to profiles outside US, AU, NZ, SG, CA, MY [S9]. For the funding endpoint, Wise says SCA "most likely applies" to UK and EEA profiles [S10]. The token description adds "PSD2 restrictions apply for EU/UK users" [S4]. When SCA is needed, Wise answers `403` with `x-2fa-approval` headers [S11][S12].
- The old fix was to sign a one-time token with your own key [S17][S18]. Today's personal-token guide does not offer it [S6]. A user report from 2 October 2026 says Wise now refuses it for personal accounts [S19]. That report says business accounts are not affected, but the issue it cites does not show that [S20]. **Treat signing as not available.**
- (b) **Sandbox: the docs do not say.** What we know:
  - The rule in [S6] and [S7] has no sandbox exception.
  - In the sandbox, SCA by SMS, phone or WhatsApp is not supported, and SCA "can be disabled via your client credentials" [S13]. Personal-token users have no client credentials [S5].
  - "SCA is off by default in the sandbox" comes from 2020 docs for the retired V1 sandbox [S17]. Do not trust it now.
  - No Stack Overflow answer or community report about the V2 sandbox was found.
  - So **only experiment E2 (step 7) can answer this.**
- (c) **Everyone else:** create the transfer by API, then "Log into the Wise account to fund the transfer". Batch groups work the same way [S7]. A partnership is the other route [S6]. Community code gives the same advice [S21].
- Simulation needs funding first [S14]. If the UK profile cannot fund by API, fund in the sandbox web UI, then continue the simulations by API.

| | UK (Sole Trader) | MY or SG |
|---|---|---|
| Sandbox stability | The only business setup Wise lists as most stable [S13] | Not listed. Wise says to fall back to UK if other regions fail [S13] |
| API funding with a personal token (official rule) | Not allowed [S6][S7] | Allowed [S6][S7] |
| Does the rule apply in the sandbox? | Unknown (E2) | Unknown (E2) |
| If API funding fails | Fund in web UI, then simulate by API [S7][S14] | Same |

Roadmap correction: section 2 fact 5 and Step 0.3 say "UK is the most stable". For **business** profiles, the live docs say "UK (Sole Trader)" [S13].
Roadmap correction (02-dashboard-rnd.md, F5 and E3): it says it is "unverified" whether a personal token can create profile webhook subscriptions. The SMB guide now tells personal-token users to "create a profile webhook subscription" to track transfers [S7]. The public HTTPS URL is still needed.
Roadmap addition (not a contradiction): Step 0.3 should mention the access level (full or read only) [S7]. Section 2 fact 4 should add that balance **statements** have the same region limit [S6].

## Decision (what you will do and why)
1. **Sandbox business profile: UK, type Sole Trader, using GBP and EUR. Proposed — confirm after the experiment.** Reasons: it is the only business setup Wise calls most stable in the sandbox [S13], and quotes, recipients, balances and simulation are the core of this project. If API funding is blocked, Wise's documented fallback (fund in the web UI) still finishes the flow [S7][S14]. The MY/SG advantage is a production rule that nobody documents for the sandbox, and MY/SG are not on the stable list [S13].
2. If E2 shows that the UK profile cannot fund by API, and you still want API funding: try adding a second business profile in SG or MY (if the sandbox allows it) and repeat **only** the funding test. Record both results. Proposed — confirm after the experiment.
3. Token access level: **full**. Reason: the project creates quotes, recipients and transfers. The current docs do not define "read only"; 2020 docs said it only lists and shows [S17]. Proposed — confirm after the experiment.
4. Keep the token in a password manager now and in a Git-ignored `.env` later. Never put it in notes, screenshots, logs, URLs or an exported Postman collection [S6].
5. Use one token for this app, created only in the sandbox [S6][S8].
6. Pick the business profile by `type == "BUSINESS"` and save its `id`. Never assume it is the first item [S3]. Store profile IDs as 64-bit integers [S4].
7. On a funding `403`, check the `x-2fa-approval` headers and `errorCode` before calling it "token broken" [S11][S12]. The dashboard gets a "Fund in Wise" link as the fallback (as in 02-dashboard-rnd.md, E2).
8. Do not build SCA signing. Reason: it is not offered for personal tokens today [S6][S19].

## Open questions
- Does the region rule apply in the V2 sandbox? Only E2 can tell (step 7).
- Can a personal token call create quote, create recipient and the simulation endpoints? The reference lists only `UserToken` (step 6) [S4][S14].
- Can one sandbox user have business profiles in two countries (UK and SG/MY)? "Create multiple business profiles" is listed for partners [S13]; the UI is not documented.
- What exactly does "read only" allow? It is not defined in the current docs.
- The token reference says "Settings > Connect and manage apps > API tokens" [S4], but the guide says "Your Account → …" [S6]. Check which menu the sandbox UI shows (step 2).
- Can a **business** account still use SCA signing? Current docs say nothing. The community claim is unproven [S19][S20].
- [S16] says personal-token logic "will be deprecated by the end of next year" for partners who move to OAuth. It does not read as a general retirement of personal tokens, but watch the changelog.
