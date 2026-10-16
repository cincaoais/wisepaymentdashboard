# 008 – Recipients and account requirements (dynamic forms)
Date: 3 October 2026
Roadmap step: Step 0.5, Q10 (also Step 0.6 requests 6–7, and Phase 4.5 wizard step 2)

## Question
Why are recipient fields different for EUR and GBP? What is a "dynamic form"?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Recipients | https://docs.wise.com/guides/product/send-money/recipients | docs.wise.com | official doc | 2026-09-16 (last updated) | Dynamic forms are "highly recommended"; "Always load a fresh set of recipient details" |
| S2 | Retrieve recipient account requirements dynamically | https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget | docs.wise.com | official doc | accessed 2026-10-03 (API version 2026Q4) | Quote-based and currency-pair variants; response fields; `Accept-Minor-Version: 1` |
| S3 | Retrieve additional recipient account requirements | https://docs.wise.com/api-reference/recipient/recipientaccountrequirementspost | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | What to do when `refreshRequirementsOnChange` is `true` |
| S4 | Create a recipient account | https://docs.wise.com/api-reference/recipient/recipientcreate | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `POST /accounts`; GBP = sort code + account number; EUR = IBAN; response fields |
| S5 | Recipient verification | https://docs.wise.com/guides/product/send-money/recipient-verification | docs.wise.com | official doc | 2026-09-04 (last updated) | Validation error shape; the IBAN `group` example quoted below |
| S6 | Recipient verification reference | https://docs.wise.com/guides/product/send-money/recipient-verification/recipient-verification-reference | docs.wise.com | official doc | 2026-09-04 (last updated) | EUR name-matching is only for Embedded/Enterprise partners |
| S7 | Recipient errors | https://docs.wise.com/guides/developer/errors/recipients | docs.wise.com | official doc | 2026-09-22 (last updated) | "Do not maintain a static list of required bank fields"; status can be 400 or 422 |
| S8 | List or create recipients (correspondent guide) | https://docs.wise.com/guides/product/send-money/use-cases/correspondent/correspondent-create-recipient | docs.wise.com | official doc, **partly outdated**: links a "Dynamic Form sandbox" on `sandbox.transferwise.tech` and shows a `validationAsync` URL on `api.sandbox.transferwise.tech` | 2026-09-16 (last updated) | Types "effectively map to a payment rail"; `key` → `details.<key>`; hard-coding allowed but risky |
| S9 | Recipient creation by target currency | https://docs.wise.com/guides/product/send-money/use-cases/correspondent/recipient-creation-by-currency | docs.wise.com | official doc | 2026-09-04 (last updated) | GBP type `sort_code`, EUR type `iban`, sample bodies |
| S10 | List recipient accounts | https://docs.wise.com/api-reference/recipient/recipientlist | docs.wise.com | official doc | accessed 2026-10-03 (2026Q4) | `GET /accounts` filters `profileId`, `currency` |
| S11 | Personal API tokens | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token | docs.wise.com | official doc | 2026-09-04 (last updated) | Personal token may retrieve and create recipients (requirements not listed) |
| S12 | Handle API errors | https://docs.wise.com/guides/developer/errors | docs.wise.com | official doc | 2026-09-22 (last updated) | "Never log tokens, client secrets, or unnecessary personal and bank data" |
| S13 | Account requirements dynamic form demo | https://docs.wise.com/guides/product/send-money/recipient-verification/account-requirements | docs.wise.com | official doc | accessed 2026-10-03 | Page loads, but it is an interactive demo with no readable text |
| S14 | Expensify/App PR #101580 "Validate, group and refresh dynamic forms from the Wise schema" | https://github.com/Expensify/App/pull/101580 | github.com | community GitHub | merged 2026-09-18; repo 5,041 stars | A large real app builds Wise forms from the schema and re-fetches it when an answer changes |
| S15 | Expensify/App PR #101579 "Add the WiseField contract and the DynamicForm registry" | https://github.com/Expensify/App/pull/101579 | github.com | community GitHub | merged 2026-09-18 | Same app masks sensitive values in drafts and confirmation screens |
| S16 | transferwise/banks-reference-android – dynamicform README | https://github.com/transferwise/banks-reference-android/blob/master/dynamicform/README.md | github.com | official GitHub, **outdated**: no commits since 2021, links old "TransferWise for Banks" docs | last commit 2021-02-02; 221 stars | Wise's own reference app renders requirement forms with regex checks and refresh-on-change |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**
Headers for every request: `Authorization: Bearer <your-token>`. Prefix: `{{base_url}}/{{api_version}}`.
1. Create a GBP → EUR quote (Step 0.6 request 5). Save `quote_id`.
2. `GET /quotes/{{quote_id}}/account-requirements` with header `Accept-Minor-Version: 1` [S2].
   Paste: every `type` value, and for the `iban` type every `fields[].group[]` item (`key`, `required`, `validationRegexp`, `refreshRequirementsOnChange`).
3. Repeat step 2 **without** `Accept-Minor-Version`. Paste only what changed (does `accountHolderName` or `email` disappear?).
4. `GET /account-requirements?source=GBP&target=EUR&sourceAmount=100` (no quote) [S2]. Is it the same as step 2?
5. Create a GBP → GBP quote and repeat step 2. Paste the `sort_code` type fields.
6. If any field in step 2 has `refreshRequirementsOnChange: true`, send `POST /quotes/{{quote_id}}/account-requirements` with a partial create-recipient body [S3]. Paste which fields were added.
7. `POST /accounts` with the EUR example body from [S9] (`"type": "iban"`, IBAN `DE89370400440532013000`, your `profile_id`).
   Paste: `id`, `type`, `accountSummary`, `longAccountSummary`, `displayFields`, and whether `confirmations` exists.
8. Break it: repeat step 7 with IBAN `DE00`. Paste the HTTP status (400 or 422?) and the `errors` array.
9. `GET /accounts?profileId={{profile_id}}&currency=EUR` [S10]. Paste the top-level shape (is there a `seekPositionForNext`?).

Example from docs [S5], not from your account – one `fields[]` entry for the IBAN field:
```json
{ "name": "IBAN",
  "group": [ { "key": "IBAN", "name": "IBAN", "type": "text",
      "refreshRequirementsOnChange": false, "required": true,
      "displayFormat": "**** **** **** **** **** **** **** ****",
      "example": "DE12345678901234567890", "minLength": 14, "maxLength": 42,
      "validationRegexp": "^[a-zA-Z]{2}[a-zA-Z0-9 ]{12,40}$",
      "validationAsync": null, "valuesAllowed": null } ] }
```

## Finding (in your own words)
**Direct answer.** Money in each currency is paid out through local bank networks ("payment rails"). Each network names a bank account in its own way. Wise models each way as a recipient `type` [S8].

| | GBP (UK local) | EUR (SEPA) |
|---|---|---|
| Recipient `type` | `sort_code` [S9] | `iban` [S9] |
| Bank fields in `details` | `sortCode` + `accountNumber` [S4] | `iban`; BIC is not required [S9] |
| Other types Wise may offer | `iban` for GB IBANs [S9] | `swift_code` (non-local) [S8] |
| Address needed? | No [S9] | No [S9] |

- The requirements are not only per currency. They depend on currency pair, country, amount, recipient type and rules that change over time [S1][S2].
- **A dynamic form is a form your app builds at run time from Wise's account-requirements response, instead of a form with hard-coded fields** [S1][S2].

**The response shape** (from [S2]). It is a list. Each item is one recipient type:
- `type`, `title`, `usageInfo`, `fields`.
- `fields[]` has a `name` and a `group[]`. Each `group[]` item is one input: `key`, `name`, `type` (UI type, e.g. `text`), `required`, `refreshRequirementsOnChange`, `displayFormat`, `example`, `minLength`, `maxLength`, `validationRegexp`, `valuesAllowed[]` (`key` + `name`, for select boxes).
- `validationAsync` is **deprecated**; Wise now validates when you submit [S2].
- `key` tells you where the value goes in the create body, e.g. `sortCode` → `details.sortCode` [S8].
- `refreshRequirementsOnChange: true` means "this answer can add fields". Re-ask with `POST /quotes/{quoteId}/account-requirements` and a partial create body [S3]. Wise's example: `address.country = US` adds `address.state` [S2].

**Which endpoint?**
- `GET /quotes/{quoteId}/account-requirements` – recommended for the quote-first flow [S2]. This is our flow.
- `GET /account-requirements?source=…&target=…&sourceAmount=…` – for recipient-first flows. Not valid for some currencies [S2].
- Send `Accept-Minor-Version: 1` so the response includes the recipient name and email fields [S2].

**Create the recipient:** `POST /accounts` with `currency`, `type`, `profile`, `accountHolderName`, `ownedByCustomer`, `details{...}` [S4]. Use the returned `id` as `targetAccount` [S1].

**"Load fresh, don't hard-code."**
- "Always load a fresh set of recipient details from the Wise API when displaying a list or specific information about the recipient" [S1].
- Not using dynamic forms "may result in your integration breaking upon a recipient requirements change" [S1]. "Do not maintain a static list of required bank fields for every currency corridor" [S7].
- But Wise also allows hard-coding, or a mix, if you plan for changes. The endpoint "is always your source of truth" [S2][S8].

**Store as little bank data as possible.**
- Never log tokens or "unnecessary personal and bank data" [S12]. Do not put rejected bank details in logs [S7].
- `longAccountSummary` is already masked ("GBP account ending in 8842"). `accountSummary` is **not** masked ("(04-00-75) 37778842") [S4].
- Real apps mask bank values in drafts and summary screens [S15]. Wise's own old reference app and Expensify both build forms from the schema [S14][S16].

**Gotchas seen in the docs**
- The request uses `"type": "sort_code"`, but the response example shows `"type": "SortCode"` [S4].
- The IBAN field `key` is `"IBAN"` in [S5], but the create examples send `details.iban` [S9]. Step 2 will show the live spelling.
- EUR name-matching ("confirmations") is for Embedded/Enterprise partners [S6]. It may not appear for you.

Roadmap correction: Section 4 (Glossary) says requirements change "per currency". That is incomplete. The docs say they also depend on the country, amount, recipient type and receiving entity, and change over time [S1][S2].
Roadmap correction: the "Account requirements (dynamic forms)" link in Step 0.4 and section 15 now opens an interactive demo with no readable text [S13]. Read the API reference [S2] instead.
Warning (Wise's own docs): [S8] still links to `sandbox.transferwise.tech` (retired 30 June 2026) and shows a deprecated `validationAsync` URL. Ignore both.

## Decision (what you will do and why)
1. Use `GET /quotes/{quoteId}/account-requirements` with `Accept-Minor-Version: 1`. Why: our flow is quote-first, and Wise recommends this variant [S2].
2. MVP route stays GBP → EUR, type `iban` (as in 02-dashboard-rnd F7). But build the recipient form from the live response for that one type: labels, `required`, `example`, length and regex. Why: no hand-typed field list to go stale [S7], and it is still small work. *Proposed — confirm after the experiment (steps 2 and 6).*
3. Only handle `refreshRequirementsOnChange` if step 2 shows a `true` field on our route. Otherwise it is a stretch goal. *Proposed — confirm after the experiment.*
4. Validate in the browser with the regex as a help only. Wise's answer is final: show each `errors[].path` next to its field [S5][S7].
5. Store only: Wise recipient `id`, `currency`, `type`, the name shown on the transfer, and `longAccountSummary`. Never store or log IBAN, sort code or account number. Fetch details live on the Recipients page. Why: [S1][S12]. *Proposed — confirm in step 7 that `longAccountSummary` is masked.*
6. In the API activity log, hide `details` in `/accounts` request and response bodies. Why: [S7][S12].

## Open questions
- Which `type` values does the sandbox return for GBP → EUR on a UK business profile? (step 2)
- Is the live IBAN key `IBAN` or `iban`? (steps 2 and 7)
- Bad IBAN: 400 or 422 in the sandbox? [S7] says either can happen. (step 8)
- Can a personal token call account-requirements? [S11] lists "retrieving and creating recipients" but does not name requirements; [S2] lists only `UserToken`. (step 2 will show it)
- Does the sandbox check IBANs like production? The docs do not say.
- The demo page [S13] could not be read as text. Open it in a browser to see a working dynamic form.
