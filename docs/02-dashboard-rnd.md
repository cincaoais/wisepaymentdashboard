# R&D 02: What dashboard should I build?

| | |
|---|---|
| **Date** | 2 October 2026. Updated 3 October 2026 with corrections from [rnd/001–013](rnd/) |
| **Status** | Decided. Option B, "Payout Console" |
| **Feeds into** | Roadmap Phase 2 (DB design) and Phase 4 (pages): [01-project-roadmap.md](01-project-roadmap.md) |

This note follows the same R&D template you'll use for your own notes:
Question → Constraints → Sources → Findings → Options → Decision → Design → Open experiments.

---

## 1. Question

> What is the **simplest** dashboard that still shows the **real** Wise send-money workflow from end to end?

"Real" means a viewer can see every step Wise actually performs: quote, recipient, transfer, funding, and each status change. Nothing should be faked in the UI.

## 2. Constraints

| Constraint | Effect on the design |
|---|---|
| Built by one intern who is new to coding | Few pages, server-rendered HTML, no JavaScript framework |
| Wise **sandbox** only, personal API token | No OAuth, no multi-customer features. A single business profile |
| Sandbox is most stable for a UK (Sole Trader) business profile, GBP/USD/EUR | Use one fixed currency route for the demo |
| Personal-token funding is limited by region, and UK/EEA funding may need SCA | The dashboard must handle "funding not allowed" cleanly (see Experiment E2) |
| The API reference lists only OAuth user tokens for quotes, recipients and simulations | Prove the personal token works first (Experiment E0) |
| Webhooks need a public HTTPS URL | Polling is the default. Webhooks are a stretch goal |
| Stripe comes later | Don't hard-wire "Wise" into names that should be generic |

## 3. Sources reviewed

| # | Source | Used for |
|---|---|---|
| S1 | [Send money overview](https://docs.wise.com/guides/product/send-money) | The four-step flow |
| S2 | [Quotes guide](https://docs.wise.com/guides/product/send-money/quotes) | Quote types, 30-minute rate lock |
| S3 | [Recipients guide](https://docs.wise.com/guides/product/send-money/recipients) | Dynamic forms, "always load fresh" rule |
| S4 | [Transfer API reference](https://docs.wise.com/api-reference/transfer) | Transfer fields, 14-day funding window |
| S5 | [Funding guide](https://docs.wise.com/guides/product/send-money/funding), [Fund from balance](https://docs.wise.com/guides/product/send-money/funding/fund-from-balance) | Funding methods, insufficient-funds response |
| S6 | [Transfer statuses](https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses) | Full status list, happy and unhappy paths, friendly labels |
| S7 | [Simulation API](https://docs.wise.com/api-reference/simulation) | Sandbox transitions and their rules |
| S8 | [Webhooks](https://docs.wise.com/guides/developer/webhooks), [Event handling](https://docs.wise.com/guides/developer/webhooks/event-handling) | Delivery rules, signature, retries |
| S9 | [Personal API token](https://docs.wise.com/guides/developer/auth-and-security/personal-api-token) | What a personal token can and can't do |
| S10 | [Environments](https://docs.wise.com/guides/developer/environments) | Sandbox URLs, supported regions and currencies |
| S11 | [Wise Help: how do I track my transfer](https://wise.com/help/articles/2977947/how-do-i-track-my-transfer) | How Wise shows tracking to its own users |
| S12 | [Balance accounts](https://docs.wise.com/guides/product/accounts/balance-accounts) | Listing and creating balances |
| S13 | [R&D notes 001–013](rnd/) | Re-checked on 3 October 2026 against the live 2026Q4 docs; source of the corrections below |

---

## 4. Findings

### F1: The real Wise send-money path

From S1. **The order matters:** each step needs an ID from the step before it.

```text
  YOU (dashboard user)          YOUR DJANGO APP                       WISE SANDBOX API
  ────────────────────          ───────────────                       ────────────────
                                                    GET  /profiles
  open dashboard  ───────────►  who am I?  ───────────────────────────►  profile list
                                                    GET  /profiles/{p}/balances
                                show money ────────────────────────────►  balances

  "send 100 GBP→EUR" ────────►  1. QUOTE   POST /profiles/{p}/quotes ──►  quote_id, rate,
                                                                          fee, expirationTime (~30 min)
  pick/add recipient ────────►  2. RECIPIENT
                                   GET  /quotes/{q}/account-requirements ► required fields
                                   POST /accounts ─────────────────────►  recipient_id
                                   PATCH /profiles/{p}/quotes/{q} ──────►  quote updated
  confirm ───────────────────►  3. TRANSFER
                                   POST /transfer-requirements ────────►  extra fields needed
                                   POST /transfers (quote + recipient
                                   + YOUR customerTransactionId) ──────►  transfer_id
                                                                          status: incoming_payment_waiting
  "pay" ─────────────────────►  4. FUND
                                   POST /profiles/{p}/transfers/{t}/payments
                                   type = BALANCE ─────────────────────►  COMPLETED / REJECTED
                                                                          status → processing
                                5. TRACK
                                   GET /transfers/{t}  (poll) ─────────►  current status
                                   or webhook transfers#state-change ◄──  Wise calls you
```

**Lesson:** a transfer is *created* in step 3, but **no money moves until step 4**. A dashboard that skips funding is not showing the real flow.

Correction (3 Oct): Wise lists `POST /transfer-requirements` between the quote PATCH and `POST /transfers` and says "always call" it. Show the price from the **patched** quote, because the recipient can change it ([rnd/003](rnd/003-send-money-flow.md)).

### F2: Transfer statuses and how Wise recommends you show them

From S6. Wise says its API status names differ from what its own app shows, and recommends these friendly labels:

| API status | Wise's recommended label | Final? | Meaning (short) |
|---|---|---|---|
| `incoming_payment_waiting` | On its way to Wise | No | Created, waiting for funds |
| `incoming_payment_initiated` | On its way to Wise | No | Funding started, money not arrived yet |
| `processing` | Processing | No | Wise has the money and is running checks |
| `funds_converted` | Processing | No | Checks done, currency converted |
| `outgoing_payment_sent` | Payment sent | **Yes** (normal end) | Wise sent it. This does **not** mean the money has arrived at the recipient's bank |
| `cancelled` | Payment cancelled | **Yes, if never funded** | Never funded. A funded transfer can go `cancelled` → `funds_refunded` |
| `bounced_back` | Bounced back | No | Recipient bank returned it |
| `funds_refunded` | Payment refunded | **Yes** | Money returned to the sender |
| `charged_back` | Funds returned to sender | Not stated | Can follow any status |
| `unknown` | Payment status unknown | No | Wise needs more information |
| `waiting_recipient_input_to_proceed` | *(none given, choose your own)* | Not stated | Only in Wise's status diagram, between `incoming_payment_waiting` and `processing`/`cancelled` |

**Happy path:** `incoming_payment_waiting → processing → funds_converted → outgoing_payment_sent`

**Unhappy path:** `outgoing_payment_sent → bounced_back → processing → cancelled → funds_refunded`

- Wise says "transfers support rollback transitions": a status can go **backwards** (e.g. `bounced_back` → `processing`). Bounce-backs can come weeks after `outgoing_payment_sent`.
- The API gives `status` as a plain string with no fixed list. Store unknown values as they are ([rnd/006](rnd/006-transfer-statuses.md)).

**Lesson:** the dashboard should show **both** the friendly label (for people) and the raw status (for you, the learner).

### F3: Funding

From S5 and S9.

- Funding from a balance needs a balance **in the same currency** as the transfer's source. Funding from a balance in another currency isn't supported.
- If the balance is too low, the body says `"status": "REJECTED"` (under HTTP 201), and the transfer stays in `incoming_payment_waiting`. The docs disagree on the code: the guide shows `transfer.insufficient_funds`, the 2026Q4 API reference shows `balance.insufficient-funds`. Handle both, and decide from the body's `status`, never the HTTP code ([rnd/005](rnd/005-funding.md)).
- In the sandbox, you add fake money with the **balance top-up simulation**.
- Personal-token funding through the API is only supported for accounts based in **US, CA, AU, NZ, SG, MY** (S9). Whether this rule is enforced in the sandbox is **unverified**; see Experiment E2.
- For UK/EEA profiles, funding is SCA-protected and can return `403` with `x-2fa-approval` headers.

### F4: Simulation rules (sandbox only)

From S7.

| Simulation | Allowed from |
|---|---|
| → `processing` | `incoming_payment_waiting` |
| → `funds_converted` | `processing` |
| → `outgoing_payment_sent` | `funds_converted` |
| → `bounced_back` | `outgoing_payment_sent` |
| → `funds_refunded` | `bounced_back` |

- **Fund the transfer first.** Even if funding already moved it to `processing`, you must still call the `/processing` simulation.
- Wait **at least 5 seconds** between simulation calls. Processing happens in the background.
- Newer simulations also exist for payout failures and delivery updates ([rnd/007](rnd/007-simulation.md)). Not needed for the MVP.

**Lesson:** a "Simulate next step" button is the clearest way to *watch* the lifecycle happen. It must only offer the valid next step.

### F5: Webhooks are not required for a good demo

From S8.

- Wise only calls **HTTPS on port 443 with a real domain**. On a laptop, that means ngrok.
- Your endpoint must reply within **5 seconds**. Every request is signed (`X-Signature-SHA256`), and events can arrive **out of order**.
- Developer Hub subscriptions need partner access. Profile-level subscriptions go through the API. Wise's SMB payouts guide tells personal-token users to create one, but the API reference lists only OAuth user tokens, so it is still **unverified** (Experiment E3).

**Lesson:** use polling (a "Refresh status" button) for the MVP and treat webhooks as a stretch goal. The status flow you show is the same either way.

### F6: Time limits the UI must respect

- **Quote:** create the transfer before `expirationTime`, about **30 minutes** (S2). The locked rate has its own `rateExpirationTime`. The review screen should show `expirationTime` and refuse an expired quote ([rnd/003](rnd/003-send-money-flow.md)).
- **Transfer:** if it isn't funded within **14 days**, it is *usually* cancelled automatically (S4).

### F7: Recipients change per currency

From S3.

- The required recipient fields depend on the currency, the country, the amount, the recipient type and the receiving entity, and they change over time. Wise recommends **dynamic forms** built from `account-requirements` ([rnd/008](rnd/008-recipients-and-account-requirements.md)).
- Wise also says to *always load fresh* recipient details from the API when displaying them.

**Lesson:** for an intern MVP, build **one fixed route**, e.g. **GBP → EUR (IBAN)**:
- One fixed route avoids building a dynamic form engine.
- Still call `account-requirements` and show its raw output on the page, so you can *see* why real apps need dynamic forms.
- Dynamic forms become a stretch goal.

### F8: How Wise shows tracking to its own users

From S11. In the Wise app you open your activity list, click a transfer, and see a **tracker**: a vertical list of steps, each with a time. That pattern (list → detail → step timeline) is the most familiar way to show a payment's life, and it maps directly onto the statuses in F2.

---

## 5. Options considered

| | **A. Balance viewer** | **B. Payout Console** ✅ | **C. Payments platform** |
|---|---|---|---|
| What it is | Read-only: profile, balances, exchange rates | Single-user console: balances, send-money wizard, transfer tracker, sandbox controls, API log | Multi-customer, OAuth, roles and approvals, reconciliation, Wise + Stripe from day one |
| Shows the real flow (F1)? | ❌ Only steps 0–1 | ✅ All of steps 1–5 | ✅ All, plus much more |
| Pages | 1–2 | 5 must-have + 2 should-have | 15+ |
| New concepts for you | HTTP GET, templates | + forms, POST, IDs across steps, idempotency, status lifecycle, error handling | + OAuth, permissions, background workers, multi-tenancy |
| Effort for a beginner | ~1 week | ~4–6 weeks | Months |
| Proves "I can connect to Wise"? | Weakly | Strongly: real transfer, real statuses | Yes, but you may never finish |
| Risk | Too shallow to learn from | Fits the scope | Too big. High chance of stalling |

### Decision: **Option B, "Payout Console"**

It's the smallest design that covers **every** step of F1 and makes each status in F2 visible. Two extra pieces make it a learning tool rather than just an app:

1. A **Sandbox panel** that lets you push a transfer through its lifecycle yourself (F4).
2. An **API activity log** that shows every request your app sent to Wise and what came back.

---

## 6. Design spec

### 6.1 Site map and priority (MoSCoW)

| Page | Priority | Teaches which Wise concept |
|---|---|---|
| Login | **Must** | Not Wise. Protects a page that can move money |
| Overview | **Must** | Profiles, balances, connection health |
| Send money (wizard) | **Must** | Quote → Recipient → Transfer → Fund (F1) |
| Transfers list | **Must** | Your local record of what you created |
| Transfer detail (timeline + sandbox panel) | **Must** | Status lifecycle (F2), simulation (F4) |
| API activity log | **Should** | What really goes over the wire |
| Recipients | **Should** | Recipient accounts, `account-requirements` (F7) |
| Webhook events | **Could** | Push vs pull (F5) |
| Dynamic recipient form for any currency | **Won't (for now)** | Too big for the MVP |

### 6.2 Layout

- A **sidebar** for navigation and a **top bar** with a coloured `SANDBOX` badge.
- Read the environment from settings, so the badge can never lie.
- **Bootstrap 5.3** with Django templates, and no JavaScript framework. A countdown for the quote expiry is the only JavaScript worth adding, and it's optional.

### 6.3 Pages

#### Page 1: Overview

- **Purpose:** "Am I connected, who am I, and how much money do I have?"
- **Data source:** **live** from Wise (profiles, balances) plus **your DB** (recent transfers, counts).
- **Wise calls:** `GET /profiles`, `GET /profiles/{p}/balances?types=STANDARD`
- **Actions:** "Top up (sandbox)", which calls the balance top-up simulation. Hide it when not in sandbox.
- **Error state:** if the token is wrong or Wise is down, show a red connection card with a friendly message, not a crash page.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Wise Payout Console                         [ SANDBOX ]   intern ▾   │
├────────────┬─────────────────────────────────────────────────────────┤
│ Overview   │  CONNECTION                                             │
│ Send money │  ● Connected  api.wise-sandbox.com / 2026Q4             │
│ Transfers  │  Profile: Test Business Ltd  (BUSINESS)  #12345678      │
│ Recipients │  Checked: 2 Oct 2026, 10:42                             │
│ API log    │                                                         │
│            │  BALANCES                                [Top up ▸]     │
│            │  ┌───────────┐ ┌───────────┐ ┌───────────┐              │
│            │  │ GBP       │ │ EUR       │ │ USD       │              │
│            │  │ 1,000.00  │ │ 0.00      │ │ 0.00      │              │
│            │  └───────────┘ └───────────┘ └───────────┘              │
│            │                                                         │
│            │  TRANSFERS   Waiting 1 · Processing 2 · Sent 5 · Other 0│
│            │  RECENT                                                 │
│            │  #T-0008  100.00 GBP → 115.80 EUR  ◐ Processing   10:30 │
│            │  #T-0007   50.00 GBP →  57.91 EUR  ● Payment sent 09:12 │
└────────────┴─────────────────────────────────────────────────────────┘
```

#### Page 2: Send money (four-step wizard)

- **Purpose:** walk through F1 one step at a time, showing what Wise returns at each step.
- **Fixed route for the MVP:** GBP → EUR, recipient by IBAN (see F7 and Experiment E4).

| Step | Screen shows | Wise call(s) | Validation you must do |
|---|---|---|---|
| 1. Amount | Source currency (GBP), target (EUR), amount | `POST /profiles/{p}/quotes` | Amount > 0, at most 2 decimal places, currency allowed |
| 2. Recipient | Pick an existing EUR recipient **or** add one (name + IBAN). A collapsible panel shows the raw `account-requirements` output | `GET /quotes/{q}/account-requirements`, `POST /accounts`, `PATCH /profiles/{p}/quotes/{q}` | Required fields present; Wise's own validation errors shown next to the field |
| 3. Review | You send, they get, rate, fee, **quote expires at hh:mm** (`expirationTime`), recipient summary | (none, uses the updated quote) | Refuse if `expirationTime` has passed. Send the user back to step 1 |
| 4. Confirm & pay | "Create transfer", then "Fund from GBP balance" | `POST /transfer-requirements`, `POST /transfers`, then `POST /profiles/{p}/transfers/{t}/payments` | Disable the button after one click. Generate `customerTransactionId` **once** for this transfer |

```text
  ① Amount ──── ② Recipient ──── ③ Review ──── ④ Confirm & pay

  ┌─ ③ Review ───────────────────────────────────────────┐
  │ You send          100.00 GBP                         │
  │ Fee                 0.52 GBP                         │
  │ Rate          1 GBP = 1.1641 EUR                     │
  │ Recipient gets    115.80 EUR                         │
  │ To                Jane Doe · IBAN …4432              │
  │ Rate locked until 11:12  (28 min left)               │
  │                                                      │
  │            [ ◂ Back ]        [ Create transfer ▸ ]   │
  └──────────────────────────────────────────────────────┘
```

After step 4, redirect to the **transfer detail** page with a success message. If funding is `REJECTED`, show the reason and a "Top up and retry" link.

#### Page 3: Transfers list

- **Purpose:** your system's own record of every transfer you created.
- **Data source:** **your DB**. A list should not trigger one API call per row.
- **Columns:** your reference, created at, source amount, target amount, recipient, status (friendly label + coloured badge), last synced.
- **Filters:** status group (Waiting / Processing / Sent / Problem).

```text
  Reference  Created           Send        Receive      Recipient   Status
  T-0008     02 Oct 10:30   100.00 GBP  115.80 EUR   Jane Doe    ◐ Processing
  T-0007     02 Oct 09:12    50.00 GBP   57.91 EUR   Jane Doe    ● Payment sent
  T-0006     01 Oct 17:40    20.00 GBP   23.15 EUR   Ali Bin A.  ○ On its way to Wise
```

#### Page 4: Transfer detail, the most important page

- **Purpose:** show one transfer's whole life. This is where you "see the workflow".
- **Data source:** your DB, plus a live `GET /transfers/{t}` when you press **Refresh**.
- **Sections:**
  1. **Summary:** amounts, rate, recipient, friendly status + raw status.
  2. **Timeline:** one row per step, with the time it happened (the tracker pattern from F8).
  3. **IDs panel (for learning):** your ID, `customerTransactionId`, Wise transfer ID, quote ID, recipient ID, profile ID.
  4. **Sandbox panel** (only in sandbox): "Fund from balance" (if not funded), then **"Simulate → next status"**. Only the valid next step is enabled (see 6.4).
  5. **Status history:** every status change you have recorded, where it came from (refresh / command / webhook), and when.

```text
┌─ Transfer T-0008 ─────────────────────────────── ◐ Processing (processing) ┐
│ 100.00 GBP → 115.80 EUR   rate 1.1641   to Jane Doe (IBAN …4432)           │
├────────────────────────────────────────┬───────────────────────────────────┤
│ TIMELINE                               │ IDs                               │
│ ✔ Transfer created        10:30:02     │ Ours ............ 8               │
│ ✔ Funded from GBP balance 10:30:15     │ customerTxnId ... 54a6bc09-…      │
│ ◐ Processing (checks)     10:30:21     │ Wise transfer ... 16521632        │
│ ○ Converted to EUR                     │ Wise quote ...... 8fa9be20-…      │
│ ○ Sent to recipient's bank             │ Recipient ....... 8692237         │
├────────────────────────────────────────┴───────────────────────────────────┤
│ SANDBOX  [ Simulate → funds_converted ]  (wait 5 s between steps)         │
│ [ ↻ Refresh status from Wise ]                     Last synced 10:30:21    │
├────────────────────────────────────────────────────────────────────────────┤
│ HISTORY  10:30:02 incoming_payment_waiting  (create)                       │
│          10:30:15 processing                (refresh)                      │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Page 5: API activity log (Should)

- **Purpose:** see the real traffic between your app and Wise. This is the best debugging and learning tool in the project.
- **Columns:** time, method, path (**no token, no full bank details**), HTTP status, duration (ms), correlation ID, linked transfer (if any), short error.
- **R&D for you:**
  - Where do you record this so that **every** Wise call is captured without copy-pasting code into each function?
  - What must never be stored here?

```text
  Time      Method  Path                                   Status  ms   Transfer
  10:30:21  GET     /2026Q4/simulation/transfers/…/process  200    412  T-0008
  10:30:15  POST    /2026Q4/profiles/…/transfers/…/payments 201    655  T-0008
  10:30:02  POST    /2026Q4/transfers                       200    590  T-0008
  10:29:40  PATCH   /2026Q4/profiles/…/quotes/…             200    301  —
```

#### Page 6: Recipients (Should)

- Live list from Wise (`GET /accounts`), following the "always load fresh" rule from F7.
- An "Add recipient" button reuses wizard step 2.

#### Page 7: Webhook events (Could)

- Only if Phase 5.2 works.
- Shows received events: delivery ID, event type, occurred at, signature OK?, processed?

### 6.4 Status → UI mapping

Use this table when you build badges, the timeline and the sandbox buttons.

| API status | Label (F2) | Badge | Timeline step reached | Sandbox "next" button |
|---|---|---|---|---|
| `incoming_payment_waiting` | On its way to Wise | grey | 1 Created | **Fund from balance**, then → `processing` |
| `incoming_payment_initiated` | On its way to Wise | grey | 1 Created | (wait / refresh) |
| `processing` | Processing | blue | 2 Funded, 3 Processing | → `funds_converted` |
| `funds_converted` | Processing | blue | 4 Converted | → `outgoing_payment_sent` |
| `outgoing_payment_sent` | Payment sent | green | 5 Sent | (optional unhappy path) → `bounced_back` |
| `bounced_back` | Bounced back | orange | problem branch | → `funds_refunded` |
| `funds_refunded` | Payment refunded | orange | final | none |
| `cancelled` | Payment cancelled | red | final if never funded; otherwise wait for `funds_refunded` | none |
| `charged_back` | Funds returned to sender | red | problem branch | none |
| `unknown` | Payment status unknown | yellow | problem branch | none |
| `waiting_recipient_input_to_proceed` | your own label | yellow | problem branch | none |

Build the timeline from **status-history rows in time order**, not from "highest step reached". Statuses can roll back (F2), and webhooks can arrive out of order (F5).

**R&D question for you:** after funding, the transfer may already show `processing`, but F4 says you still call the `/processing` simulation. How will your sandbox panel know whether that call has been made? (Hint: what would you record?)

### 6.5 What the dashboard needs to show

This is **input for your Phase 2 DB chart**. It lists *information*, not tables. Deciding the tables, columns and which items to store vs fetch live is your job.

| Information | Shown on | Hint: store or fetch live? |
|---|---|---|
| Profile name, type, Wise profile ID | Overview | Changes rarely. Think about it |
| Balances per currency | Overview | Changes often (F3) |
| Your own transfer reference | List, detail | Yours. You need it forever |
| Who created the transfer, and when | List, detail | Yours |
| Send amount + currency, receive amount + currency, rate, fee | Wizard, list, detail | Must stay as they were at creation time |
| Quote ID, `expirationTime`, `rateExpirationTime` | Wizard, detail | Lives only ~30 min (F6), but the ID is history |
| Recipient display name + masked account | List, detail | F7 says load fresh. What's the minimum you need for the list page? |
| Wise transfer ID, quote ID, recipient ID, profile ID | Detail (IDs panel) | Links your rows to Wise's |
| `customerTransactionId` | Detail | Must exist *before* the Wise call. Unique |
| Current status + last synced time | List, detail | Yours, updated by refresh/command/webhook |
| Status history (status, time, source) | Detail | Yours |
| Funding result (COMPLETED / REJECTED + reason) | Detail | ? |
| API call log rows | API log page | Yours. Never the token |
| Webhook events (delivery ID, type, payload, verified?) | Webhook page | Yours (stretch) |
| Provider (Wise now, Stripe later) | List filter (Phase 7) | Plan for it now |

### 6.6 The five-minute demo story

What you'll show your supervisor:

1. **Overview:** "Connected to the Wise sandbox, here's my business profile and GBP balance."
2. **Top up:** add 1,000 GBP with the sandbox top-up, and the balance changes.
3. **Send money:** 100 GBP → EUR. Show the quote, the rate expiry, the recipient requirements, then create the transfer.
4. **Fund** from the GBP balance. The status changes from "On its way to Wise" to "Processing".
5. **Simulate** `processing` → `funds_converted` → `outgoing_payment_sent`, refreshing each time. The timeline fills in.
6. **API log:** "Here's every request my app sent to Wise, and what came back."
7. (Bonus) **Unhappy path:** simulate `bounced_back` → `funds_refunded`, and show the problem badge.

### 6.7 Non-goals

Leave these out on purpose, to keep the project finishable:

- Multiple users or customers with separate Wise accounts (OAuth).
- Roles and approval workflows.
- Dynamic forms for every currency.
- Production deployment.
- Statements, reconciliation, cards, receiving money.

---

## 7. Open experiments (run in Phase 0)

Record each result in its own `docs/rnd/` note. **E1–E4 can change the design**, so run them before Phase 2.

| ID | Experiment | If it fails |
|---|---|---|
| **E0** (run first) | Can your personal token create a quote, get account requirements, create a recipient and call the simulations? The API reference lists only OAuth user tokens for these | Write down the exact error and tell Claude. The whole design depends on it |
| **E1** | Can you self-register at `wise-sandbox.com`, create a business profile, and generate a personal token? | Email `api@wise.com` for sandbox access. Tell Claude so we can re-plan |
| **E2** | With your profile's country, does **fund from balance** via the API succeed? (Try a UK Sole Trader profile first. Note any `403` with `x-2fa-approval` headers. If it's refused, try a MY or SG business profile) | Fund the transfer in the sandbox **web UI** instead, then continue with the simulation via the API. The dashboard shows a "Fund in Wise" link instead of a button |
| **E3** | Can a personal token create a **profile-level webhook** subscription? | Stay with polling. Webhooks page becomes "Won't" |
| **E4** | Does **GBP → EUR (IBAN)** work end to end? | Fall back to **GBP → GBP** (sort code + account number) |
| **E5** | Right after funding, what status does `GET /transfers/{t}` show? Does the `/processing` simulation still succeed? | Write down the exact behaviour. It decides how the sandbox panel works (6.4) |

---

## 8. Stripe later: how this design grows

- The **Transfers list** becomes a "Transactions" list with a **provider** column and filter.
- A new **"Receive payment"** page creates a Stripe Checkout Session or PaymentIntent in test mode.
- **Transfer detail** gets a Stripe version: PaymentIntent statuses instead of Wise statuses, in the same timeline layout.
- The **API log** records calls from both providers.
- If your Phase 2 schema and Phase 3 client follow 6.5's "Provider" row, none of the existing Wise pages need to change.

---

## 9. Sources

- Wise: [Send money](https://docs.wise.com/guides/product/send-money) · [Quotes](https://docs.wise.com/guides/product/send-money/quotes) · [Recipients](https://docs.wise.com/guides/product/send-money/recipients) · [Account requirements (API reference)](https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget) · [Transfer API](https://docs.wise.com/api-reference/transfer) · [Funding](https://docs.wise.com/guides/product/send-money/funding) · [Fund from balance](https://docs.wise.com/guides/product/send-money/funding/fund-from-balance) · [Transfer statuses](https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses) · [Simulation API](https://docs.wise.com/api-reference/simulation) · [Webhooks](https://docs.wise.com/guides/developer/webhooks) · [Event handling](https://docs.wise.com/guides/developer/webhooks/event-handling) · [Personal API token](https://docs.wise.com/guides/developer/auth-and-security/personal-api-token) · [Environments](https://docs.wise.com/guides/developer/environments) · [Balance accounts](https://docs.wise.com/guides/product/accounts/balance-accounts)
- Detailed, re-checked notes: [rnd/001–013](rnd/)
- Wise Help Centre: [How do I track my transfer?](https://wise.com/help/articles/2977947/how-do-i-track-my-transfer)
- UI: [Bootstrap 5.3](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
