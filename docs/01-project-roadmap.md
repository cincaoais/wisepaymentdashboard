# Wise Payment Dashboard: Project Roadmap

| | |
|---|---|
| **Project** | Django dashboard connected to the Wise sandbox |
| **Learning mode** | Hand-coding. You write every line; Claude mentors, reviews, and quizzes |
| **Last updated** | 3 October 2026 (corrections from the R&D notes in `docs/rnd/`) |
| **Companion docs** | [02-dashboard-rnd.md](02-dashboard-rnd.md): what the dashboard should look like and why · [03-postman-guide.md](03-postman-guide.md): how to run the Wise flow in Postman · [rnd/](rnd/): R&D notes 001–013 |

---

## Contents

1. [How to use this document](#1-how-to-use-this-document)
2. [Key facts to know before you start](#2-key-facts-to-know-before-you-start)
3. [Your starting point](#3-your-starting-point)
4. [Glossary](#4-glossary)
5. [How to do R&D](#5-how-to-do-rd)
6. [Phase 0: Preparation (no Django code)](#phase-0-preparation-no-django-code)
7. [Phase 1: Project foundation](#phase-1-project-foundation)
8. [Phase 2: Database design](#phase-2-database-design)
9. [Phase 3: Wise client (service layer)](#phase-3-wise-client-service-layer)
10. [Phase 4: Dashboard pages](#phase-4-dashboard-pages)
11. [Phase 5: Keeping statuses up to date](#phase-5-keeping-statuses-up-to-date)
12. [Phase 6: Hardening and demo](#phase-6-hardening-and-demo)
13. [Phase 7: Stripe (future)](#phase-7-stripe-future)
14. [Testing strategy](#14-testing-strategy)
15. [Documentation index](#15-documentation-index)
16. [Progress log](#16-progress-log)

---

## 1. How to use this document

Every step uses the same layout:

| Part | Meaning |
|---|---|
| **Goal** | What this step achieves, in one sentence |
| **Read first** | Docs to read *before* you touch anything |
| **Do** | The actions, in order |
| **Test before moving on** | What you must check before the next step |
| **Done when** | A checkbox you can honestly tick |
| **Ask yourself** | Quiz questions. If you can't answer one, go back and re-read |

### Mentoring rules

- **You type all the code.** Claude does not write project code for you.
- **Getting a review:** tell Claude the file path. Claude reads it, points to the line and explains *why* it's wrong, without giving you a fixed version.
- **Getting help when stuck.** Hints escalate in three levels:
  1. A question that points you in the right direction.
  2. The exact doc section to read.
  3. The steps in plain English (pseudocode level).

  You only get real code if you explicitly say **"show me"**.
- **SQL** is the exception: once your DB chart is ready, Claude will guide you through the PostgreSQL commands.
- **Phase gates:** at the end of every phase, Claude quizzes you. You move on only when you can explain your own code.

---

## 2. Key facts to know before you start

These were verified against the official docs on 1–2 October 2026.

1. **Wise is a payout API, not a checkout API.**
   - Wise's API is mainly for **sending money out**: quotes, recipients, transfers and balances.
   - Stripe is for **taking money in**: cards and checkout pages.
   - Your database and code should leave room for both (see Phase 7).
2. **The old Wise sandbox is gone.**
   - `sandbox.transferwise.tech` and `sandbox.wise.tech` were deprecated on **30 June 2026**.
   - Most YouTube videos and blog posts still use those URLs. Ignore them.
   - Use these instead:

   | | URL |
   |---|---|
   | Sandbox web UI | `https://wise-sandbox.com` |
   | Sandbox API | `https://api.wise-sandbox.com` |
   | Production API | `https://api.wise.com` |

3. **API paths start with a version.**
   - Wise uses calendar versioning, for example `https://api.wise-sandbox.com/2026Q4/profiles`.
   - A new version is released every quarter. `2026Q4` became **Latest** on 1 October 2026.
   - Old tutorials use "legacy" paths like `/v1/...` or `/v3/...`.
   - Pick one style and stay consistent.
4. **Personal API tokens belong to a business account.**
   - A personal token can create quotes, recipients and transfers, and track transfer events.
   - **Funding a transfer through the API** with a personal token is only allowed for accounts based in **US, CA, AU, NZ, SG or MY**. Balance statements have the same limit. Everyone else funds in the Wise website.
   - For UK/EEA profiles, funding can also need Strong Customer Authentication (a `403` with `x-2fa-approval` headers). Whether either rule applies in the sandbox is unverified. See [rnd/002](rnd/002-profiles-and-tokens.md) and [rnd/005](rnd/005-funding.md).
   - The API reference lists only OAuth user tokens for quotes, recipients and simulations, while the token guide says personal tokens can do these. **Test this first** in Postman ([rnd/007](rnd/007-simulation.md)).
5. **The sandbox is most stable for UK (Sole Trader) business profiles with GBP, USD or EUR.** Other routes may fail.
6. **The simulation API is your best friend.**
   - In the sandbox you can top up a balance and push a transfer through its statuses.
   - Rule: **fund the transfer first, then simulate**.
   - Wait **at least 5 seconds** between simulation calls.
7. **Time limits:**
   - A quote has two times. Create the transfer before `expirationTime` (about **30 minutes**). The locked rate ends at `rateExpirationTime`. See [rnd/003](rnd/003-send-money-flow.md).
   - A transfer that isn't funded within **14 days** is *usually* cancelled automatically.

---

## 3. Your starting point

Checked on 1 October 2026:

| Item | State | Note |
|---|---|---|
| Python | 3.14.2 | Inside `.venv` |
| Virtual env | `.venv`, created with **uv** | There is no `pip` inside it. Add packages with `uv add <package>` (see Step 1.2) |
| Django | 6.1.1 | Project `wisepaymentdashboard/` already created |
| Database | SQLite (default) | Switch to Postgres in Phase 1 |
| PostgreSQL | 18.4 (Homebrew), running | `brew services list` shows it started |
| Git | Installed, **repo not created yet** | Do this first (Step 0.1) |
| `SECRET_KEY` | Hardcoded in `settings.py` | Move to `.env` in Phase 1 |

---

## 4. Glossary

You must be able to explain each of these in your own words before Phase 3.

| Term | Starting definition (expand it in your R&D notes) |
|---|---|
| **Sandbox** | Wise's test environment with fake money |
| **Personal API token** | A secret key that lets your app act as your Wise business account |
| **Profile** | The personal or business identity that owns balances, recipients and transfers. Almost every call needs a `profileId` |
| **Balance** | Money held in one currency inside the profile's multi-currency account |
| **Quote** | Wise's offer: "send X of currency A, recipient gets Y of currency B, at this rate and fee". It expires |
| **Recipient (account)** | The bank account receiving the money. Wise calls it `targetAccount` in a transfer |
| **Account requirements** | The list of fields a recipient needs (IBAN, sort code, ...). It changes with the currency, country, amount, recipient type and receiving entity, and over time |
| **Transfer** | The payment order, built from a quote and a recipient |
| **Funding** | Paying for the transfer, for example from your balance. Nothing moves until this happens |
| **Transfer status** | Where the transfer is in its life: `incoming_payment_waiting` → `processing` → `funds_converted` → `outgoing_payment_sent` |
| **`customerTransactionId`** | A UUID *you* generate for each transfer, so a retry can't create a duplicate. This idea is called **idempotency** |
| **Simulation** | Sandbox-only endpoints that fake real-world events (top-ups, status changes) |
| **Webhook** | Wise calling *your* server when something changes |
| **Polling** | *You* asking Wise "has it changed yet?" on a timer or button press |
| **`Decimal`** | Python's decimal number type. Exact for numbers like 0.1, but still rounds results that need more than 28 digits (like 1/3). Use it for money, never `float` |

---

## 5. How to do R&D

### The R&D loop

```text
1. QUESTION    →  write the exact thing you need to know
2. READ        →  official docs first (links in section 15)
3. EXPERIMENT  →  try it by hand (Postman, psql, Django shell)
4. RECORD      →  write what happened, paste request + response (remove the token)
5. DECIDE      →  write the decision and why
```

### Rules

- **Rule 1: Never write Python for an API call you haven't made by hand in Postman first.**
- **Rule 2: Trust sources in this order:**
  1. Official docs.
  2. Official GitHub repos.
  3. Stack Overflow.
  4. Blogs and videos.
- **Rule 3: Check the date of every source.** Anything that mentions `transferwise.tech` is out of date.
- **Rule 4: Time-box each question to 30–60 minutes.** If you're still stuck, write down what you tried and bring it to a session.
- **Rule 5: Never paste a real token** into notes, screenshots, chat or Git.

### Where notes live

```text
docs/
├── 01-project-roadmap.md      ← this file
├── 02-dashboard-rnd.md        ← dashboard research
└── rnd/
    ├── 001-wise-environments.md
    ├── 002-profiles-and-tokens.md
    └── ...
```

### Template for each R&D note

```text
# NNN – <topic>
Date:
## Question
## Sources (links)
## Experiment (request, response, screenshots – token removed)
## Finding (in your own words)
## Decision (what you will do and why)
## Open questions
```

---

## Phase 0: Preparation (no Django code)

### Step 0.1: Put the project under Git

- **Goal:** every change from now on is tracked and can be undone.
- **Read first:**
  - [gitignore docs](https://git-scm.com/docs/gitignore)
  - [GitHub's Python .gitignore template](https://github.com/github/gitignore/blob/main/Python.gitignore)
- **Do:**
  1. Run `git init` in the workspace root (the folder that contains `.venv`).
  2. Write a `.gitignore`. For each file, ask three questions:
     - Is it **secret**?
     - Is it **generated**?
     - Is it **only true on my machine**?

     If any answer is yes, ignore it.
  3. Make your first commit.
- **Test before moving on:** `git status` must not list `.venv`, `db.sqlite3`, `__pycache__` or any `.env` file.
- **Done when:**
  - [ ] Repo created, `.gitignore` committed, `git status` is clean.
- **Ask yourself:** why must `.env` never be committed, even in a private repo?

### Step 0.2: Install your tools

- **Goal:** you can make HTTP requests and look inside Postgres without writing code.
- **Do:**
  1. Install [Postman](https://www.postman.com/downloads/).
  2. Read [Postman environments](https://learning.postman.com/docs/sending-requests/variables/managing-environments/).
  3. Check that you can open `psql` (it comes with Postgres). [psql docs](https://www.postgresql.org/docs/current/app-psql.html).
  4. Optional: a database GUI such as pgAdmin, DBeaver or TablePlus.
- **Done when:**
  - [ ] Postman opens.
  - [ ] You can connect with `psql` and run `\l` to list databases.

### Step 0.3: Create your Wise sandbox account and token

- **Goal:** you have a sandbox business profile and an API token.
- **Read first:**
  - [Environments](https://docs.wise.com/guides/developer/environments)
  - [Personal API token](https://docs.wise.com/guides/developer/auth-and-security/personal-api-token)
  - [About profiles](https://docs.wise.com/guides/product/account-setup/about-profiles)
- **Do:**
  1. Sign up at [wise-sandbox.com](https://wise-sandbox.com).
  2. Create a **business** profile. Write down which country you chose and why.

     This is a trade-off:
     - **UK, type Sole Trader** is the most stable business profile in the sandbox.
     - **MY or SG** is where a personal token may fund transfers through the API.

     Record it in R&D note `002`.
  3. Go to **Your Account → Connect and manage apps → API tokens** and generate a token with **full** access (the other choice is read only). The sandbox 2FA code is always `111111`. The token is shown **once**.
  4. Store the token in a password manager, **not** in a file inside the project.
- **Test before moving on:** you can log in to the sandbox UI and see your business profile.
- **If signup is blocked:**
  1. Write down exactly what happened (screenshot the error).
  2. Email `api@wise.com` and ask for sandbox access as an individual developer.
  3. Tell Claude. We'll plan around it.
- **Done when:**
  - [ ] Sandbox business profile exists.
  - [ ] Token is stored safely.

### Step 0.4: Reading list (in this order)

- **Goal:** understand the whole send-money path before building any of it.
- **Do:** read these and take notes as you go.
  1. [Sandbox V2 migration](https://docs.wise.com/guides/developer/environments/sandbox-v2-migration): why old tutorials break.
  2. [Global versioning](https://docs.wise.com/guides/developer/global-versioning): the `/2026Q4/` part of the URL.
  3. [Send money overview](https://docs.wise.com/guides/product/send-money): the four-step flow.
  4. [Quotes](https://docs.wise.com/guides/product/send-money/quotes)
  5. [Recipients](https://docs.wise.com/guides/product/send-money/recipients) and [Account requirements (API reference)](https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget). The old account-requirements guide page is now an interactive demo with no readable text.
  6. [Transfers](https://docs.wise.com/guides/product/send-money/transfers) and [Standard transfers](https://docs.wise.com/guides/product/send-money/standard-api-transfers)
  7. [Funding](https://docs.wise.com/guides/product/send-money/funding) and [Fund from balance](https://docs.wise.com/guides/product/send-money/funding/fund-from-balance)
  8. [Transfer statuses](https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses)
  9. [Simulation API](https://docs.wise.com/api-reference/simulation)
  10. [Errors](https://docs.wise.com/guides/developer/errors)
  11. [Webhooks overview](https://docs.wise.com/guides/developer/webhooks). Skim for now; you'll need it in Phase 5.
- **Done when:**
  - [ ] You can draw the quote → recipient → transfer → fund → status flow from memory.

### Step 0.5: R&D questions

- **Goal:** answer these in `docs/rnd/` notes **before** Phase 1.
- **Do:** answer each question in your own words, citing the doc link.

| # | Question | Hint: where to look |
|---|---|---|
| 1 | What are the sandbox and production base URLs? What does `2026Q4` in the path mean, and what happens on 1 January 2027? | Environments, Global versioning |
| 2 | What is a profile? Why does almost every endpoint need a `profileId`? | About profiles, Profile API |
| 3 | What order do you create quote, recipient and transfer in? Which ID from each step does the next step need? | Send money overview |
| 4 | Why do you update ("PATCH") a quote with the recipient before creating the transfer? | Quotes guide |
| 5 | What does `customerTransactionId` do? What happens if you send the same one twice? | Transfer API reference |
| 6 | Can you fund a transfer from a balance in a *different* currency? | Funding guide |
| 7 | What does the funding call return when the balance is too low? What status is the transfer left in? | Fund from balance |
| 8 | List every transfer status. Which are **final**? Which friendly label does Wise recommend for each? | Transfer statuses |
| 9 | Which simulation transitions exist, in which order, and what must happen before the first one? | Simulation API |
| 10 | Why are recipient fields different for EUR and GBP? What is a "dynamic form"? | Recipients, Account requirements |
| 11 | What does a Wise error response look like? How should your app react to 401 vs 422 vs 500? | Errors guide |
| 12 | Why must money never be a `float`? Prove it in a Python shell with `0.1 + 0.2`. | [Python decimal](https://docs.python.org/3/library/decimal.html) |
| 13 | Webhooks vs polling: what does each need from your setup (a public URL? HTTPS?), and which is easier to start with? | Webhooks overview |

- **Done when:**
  - [ ] 13 questions answered with links.
  - [ ] You've reviewed them with Claude.

### Step 0.6: Run the whole flow by hand in Postman

- **Goal:** prove that the connection and the whole flow work *before* any Django code exists.
- **Read first:**
  - [03-postman-guide.md](03-postman-guide.md): Postman setup, token safety, scripts that save IDs, and every request below with its headers.
  - Each endpoint's API reference page (links in section 15).
  - Optional: Wise's official [Send money Postman collection](https://elements.getpostman.com/view/fork?collection=24215266-639bb28a-dbc1-45e6-aca1-e58a86db34a3&workspaceId=a247415a-a90f-4b3c-88d2-14aa27592db4). Study it, but build your own collection so you understand every request.
- **Do:**

  **1. Create a Postman environment** called `Wise Sandbox` with these variables:

  | Variable | Value |
  |---|---|
  | `base_url` | `https://api.wise-sandbox.com` |
  | `api_version` | `2026Q4` |
  | `token` | your token, stored the way the Postman guide recommends. Never in an exported file |
  | `profile_id`, `balance_id`, `quote_id`, `recipient_id`, `transfer_id`, `customer_transaction_id` | fill these in as you go |

  **2. Build these requests in order.** For each one, read its API reference page and work out the body yourself, then compare with the Postman guide.

  Before request 5, check that your personal token is allowed on the quote, recipient and simulation endpoints. The API reference lists only OAuth user tokens for them ([rnd/007](rnd/007-simulation.md), experiment step 1).

  | # | What | Endpoint (prefix `{{base_url}}/{{api_version}}`) | Save from response |
  |---|---|---|---|
  | 1 | List profiles | `GET /profiles` | business `profile_id` |
  | 2 | List balances | `GET /profiles/{profileId}/balances?types=STANDARD` | `balance_id` for your source currency |
  | 3 | Create a balance (only if you have none) | `POST /profiles/{profileId}/balances`, with the required header `X-idempotence-uuid: <new UUID>` | `balance_id` |
  | 4 | Top up the balance (sandbox only) | Simulation: balance top-up | new balance amount |
  | 5 | Create a quote (e.g. GBP 100 → EUR) | `POST /profiles/{profileId}/quotes` | `quote_id`, rate, fee, expiry |
  | 6 | Get recipient requirements | `GET /quotes/{quoteId}/account-requirements`, with header `Accept-Minor-Version: 1` | the required fields |
  | 7 | Create a recipient | `POST /accounts` | `recipient_id` |
  | 8 | Attach the recipient to the quote | `PATCH /profiles/{profileId}/quotes/{quoteId}`, body sent as `application/merge-patch+json` with `targetAccount` | updated fee/amount. Show *this* price, not the first quote's |
  | 8b | Check transfer requirements | `POST /transfer-requirements` (Wise says "always call" it) | extra `details` fields the transfer needs |
  | 9 | Create the transfer | `POST /transfers` (generate a fresh UUID for `customerTransactionId`) | `transfer_id`, status |
  | 10 | Fund it from the balance | `POST /profiles/{profileId}/transfers/{transferId}/payments` | funding `status`. Trust the body (`COMPLETED`/`REJECTED`), not the HTTP code. If funding is refused (country rule, or a `403` asking for 2FA), fund in the sandbox website and continue with 11 ([rnd/005](rnd/005-funding.md)) |
  | 11 | Simulate: `processing` | `GET /simulation/transfers/{transferId}/processing` | status |
  | 12 | Wait 5 s, simulate: `funds_converted` | same endpoint, different status | status |
  | 13 | Wait 5 s, simulate: `outgoing_payment_sent` | same endpoint, different status | status |
  | 14 | Get the transfer | `GET /transfers/{transferId}` | final status |

  **3. Break it on purpose** and record what Wise returns for each:
  - **Wrong token.**
  - **Expired or invalid quote ID.**
  - **Bad IBAN.**
  - **Duplicate `customerTransactionId`:** send step 9 twice with the same UUID.
  - **Funding with too little balance.**
  - **Simulating before funding.**
  - **Simulating two steps with no wait in between.**

  **4. Export the collection** (without the environment, because it holds the token) to `docs/postman/`.
- **Test before moving on:** you can run requests 1–14 (and 8b) again from scratch without looking at your notes.
- **Done when:**
  - [ ] Full flow reaches `outgoing_payment_sent`.
  - [ ] All seven "break it" experiments are recorded.
  - [ ] Collection exported with no token inside.
- **Ask yourself:**
  - If step 9 times out and you don't know whether it worked, what do you do?
  - How does `customerTransactionId` save you?

> **Phase 0 gate:** explain the full flow to Claude out loud (in text), step by step, including what each ID is for.

---

## Phase 1: Project foundation

### Step 1.1: Decide the project structure

- **Goal:** know where every future file will live *before* you create it.
- **Read first:**
  - [Django tutorial part 1](https://docs.djangoproject.com/en/stable/intro/tutorial01/), especially "projects vs apps".
  - [12-factor config](https://12factor.net/config)
- **Do:** answer these in R&D note `0xx-project-structure.md`:
  1. One Django app or two? (For example, one app for payment data and logic, and one for dashboard pages.) Justify your choice.
  2. Where will the code that talks to Wise live? It must be **one place only**. Why?
  3. When Stripe arrives, where will its code go? Your structure should make that obvious.
- **Done when:**
  - [ ] A folder tree is drawn in your note and reviewed with Claude.

### Step 1.2: Install packages

- **Goal:** install only what you need, and know why each package is there.
- **Read first:**
  - [uv projects: init](https://docs.astral.sh/uv/concepts/projects/init/), [dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/), [sync](https://docs.astral.sh/uv/concepts/projects/sync/)
  - [rnd/013](rnd/013-python-packages.md): versions, test results and why there are more packages than you asked for.
- **Do:** from the workspace root, use uv's project mode so `uv sync --all-groups` can rebuild the environment anywhere:
  1. `uv init --bare --python 3.14` creates `pyproject.toml` only.
  2. `uv add django 'psycopg[binary]' django-environ requests`. Include `django`: `uv sync` removes anything not in `uv.lock`. Keep the quotes, because zsh treats `[binary]` as a filename pattern.
  3. `uv add --dev pytest-django responses`. Test-only tools go in the `dev` group.
  4. `uv sync --all-groups`.

  For each package, open its docs and write one line on what it does:

  | Package | Used for | Docs |
  |---|---|---|
  | `psycopg[binary]` | Django ↔ PostgreSQL driver | [psycopg 3](https://www.psycopg.org/psycopg3/docs/) |
  | `django-environ` | Reading settings from `.env` | [django-environ](https://django-environ.readthedocs.io/en/latest/) |
  | `requests` | Calling the Wise API | [requests](https://requests.readthedocs.io/en/latest/) |
  | `pytest-django` | Running tests | [pytest-django](https://pytest-django.readthedocs.io/en/latest/) |
  | `responses` | Faking HTTP calls in tests | [responses](https://github.com/getsentry/responses) |

  From now on, add or remove packages only with `uv add` / `uv remove`. Need a `requirements.txt` for some tool? Generate it: `uv export --format requirements.txt --no-hashes --all-groups -o requirements.txt`.
- **Done when:**
  - [ ] Packages installed with `uv sync --all-groups`.
  - [ ] `pyproject.toml` and `uv.lock` committed.

### Step 1.3: Create the Postgres database and user (SQL session with Claude)

- **Goal:** your app gets its own database and its own login. It never uses the `postgres` superuser.
- **Read first:**
  - [CREATE ROLE](https://www.postgresql.org/docs/current/sql-createrole.html)
  - [CREATE DATABASE](https://www.postgresql.org/docs/current/sql-createdatabase.html)
  - [GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
  - [Django PostgreSQL notes](https://docs.djangoproject.com/en/stable/ref/databases/)
- **Do:**
  1. Choose a database name, role name and password. The password goes in your password manager and `.env`.
  2. **Try writing the statements yourself first.**
  3. Bring them to a session with Claude for review before you run them.
  4. Run them in `psql`.
- **Test before moving on:** from a terminal, log in to `psql` **as the new role**, into the new database.
- **Done when:**
  - [ ] You can log in as the app role.
  - [ ] You can explain why the app shouldn't use the superuser.

### Step 1.4: Move secrets and settings into `.env`

- **Goal:** `settings.py` contains no secrets and no machine-specific values.
- **Read first:**
  - [Django settings](https://docs.djangoproject.com/en/stable/topics/settings/)
  - [django-environ quick start](https://django-environ.readthedocs.io/en/latest/)
- **Do:**
  1. List every value in `settings.py` that is secret or differs between your laptop and a server: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, the database connection, and later the Wise token, base URL and API version.
  2. Move them to a `.env` file that Git ignores.
  3. Create a `.env.example` with the same keys and **fake values**, and commit it. Why does this file exist?
  4. Point `DATABASES` at Postgres using the env values.
- **Test before moving on:**
  - `python manage.py check` reports no issues.
  - `git status` does **not** show `.env`.
- **Done when:**
  - [ ] `git grep` for your token or password finds nothing.

### Step 1.5: First run on Postgres

- **Goal:** Django creates its built-in tables in Postgres, and you can see them.
- **Do:**
  1. `python manage.py migrate`
  2. `python manage.py createsuperuser`
  3. `python manage.py runserver`, then log in at `/admin`.
  4. In `psql`: run `\dt` to list tables, then `\d auth_user` to inspect one.
- **Test before moving on:** the admin login works, and `\dt` shows `auth_user`, `django_session` and the others.
- **Done when:**
  - [ ] Running on Postgres.
  - [ ] `db.sqlite3` is no longer used.
  - [ ] Committed.
- **Ask yourself:**
  - What is a migration?
  - Who created those tables: you or Django?
  - What is the `django_migrations` table for?

> **Phase 1 gate:** Claude reviews `settings.py`, `.gitignore`, `.env.example` and your folder tree.

---

## Phase 2: Database design

### Step 2.1: Learn the building blocks

- **Read first:**
  - [Django models](https://docs.djangoproject.com/en/stable/topics/db/models/)
  - [Model field reference](https://docs.djangoproject.com/en/stable/ref/models/fields/), especially `DecimalField`, `ForeignKey`, `choices`, `unique` and `null` vs `blank`.
  - [Postgres numeric types](https://www.postgresql.org/docs/current/datatype-numeric.html)
  - [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
  - [Indexes](https://www.postgresql.org/docs/current/indexes.html)
- **Done when:**
  - [ ] You can explain primary key, foreign key, unique constraint, index, `NULL`, and `numeric(precision, scale)`.

### Step 2.2: List the "things" in your system

- **Goal:** turn the Postman flow into a list of nouns (candidate tables).
- **Do:**
  1. Go through your Phase 0 Postman flow and list every object Wise returned.
  2. Read the **"What the dashboard needs to show"** section in [02-dashboard-rnd.md](02-dashboard-rnd.md).
  3. For each object, decide whether you **store it locally** or **fetch it live every time**, and write the reason.

  Use these questions:

  | Question | Why it matters |
  |---|---|
  | Does it change often on Wise's side (e.g. balances)? | Stored copies go stale |
  | Do I need its history even if Wise is down? | You need a local record |
  | Is it something *I* created and must be able to find again? | You need a local record |
  | Is it sensitive (bank details)? | Store as little as possible |

- **Done when:**
  - [ ] A table of objects with "store / fetch live" and a reason for each.

### Step 2.3: Draw the chart

- **Goal:** a diagram you can review before any model code exists.
- **Do:** draw it on [dbdiagram.io](https://dbdiagram.io). For every table show:
  - Columns and data types.
  - Primary key.
  - Foreign keys.
  - Unique columns.
  - Which columns can be empty.
- **Self-review checklist** (answer each one in your note):
  - [ ] Every row that mirrors a Wise object has **two IDs**. Why: yours and Wise's?
  - [ ] Every amount is stored with its **currency** right next to it, as a decimal with a precision you chose deliberately.
  - [ ] You know which status values are allowed, and where that list is enforced.
  - [ ] **Failure order:** if Wise accepts the transfer but your DB save fails, what is in each system? Which do you save first, and what do you save *before* calling Wise?
  - [ ] **Duplicate protection:** what stops the same transfer from being created twice? Which column is unique?
  - [ ] **Stripe test:** could a Stripe payment fit into your tables tomorrow without renaming anything?
  - [ ] **Audit:** do you keep a history of status changes and/or raw API responses for debugging? Where?
  - [ ] **Ownership:** can you tell which dashboard user created each transfer?
- **Done when:**
  - [ ] Chart exported (image or dbdiagram text) to `docs/db/`.

### Step 2.4: Chart review and SQL session (with Claude)

- **Goal:** turn the chart into real tables, and learn SQL along the way.
- **Do (together):**
  1. Claude reviews the chart with questions, not fixes. You revise it.
  2. **SQL practice:** create a separate practice database (e.g. `wise_sql_practice`) and hand-write `CREATE TABLE` statements for your chart there. Then practise `INSERT`, `SELECT`, `JOIN`, `UPDATE` and constraint errors. Claude guides the SQL.
  3. **Real tables:** write your Django models from the same chart.
  4. Run `python manage.py makemigrations`, then `python manage.py sqlmigrate <app> <number>` to see the SQL Django generates.
  5. **Compare** Django's SQL with your hand-written SQL. Write down every difference and explain it.
  6. Run `python manage.py migrate`, then `\d <table>` in `psql`.
- **Key rule:**
  - In the app database, **Django models and migrations are the only thing that creates or changes tables**.
  - Hand-written SQL is for setup, inspecting and learning.
  - If you create tables by hand in the app database, Django and Postgres will disagree, and migrations will break.
- **Done when:**
  - [ ] Models migrated.
  - [ ] Differences explained.
  - [ ] Chart, models and DB all match.

### Step 2.5: Register the models in the admin

- **Read first:** [Django admin](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- **Do:**
  1. Register the models.
  2. Create a few fake rows through the admin.
  3. Query them in `psql` with `SELECT` and a `JOIN`.
- **Test before moving on:** try to break a constraint, such as a duplicate unique value or a missing required field. Check that the DB refuses it.
- **Done when:**
  - [ ] Admin shows your tables.
  - [ ] You've seen a constraint error with your own eyes.

> **Phase 2 gate questions:**
> - Why `DecimalField` and not `FloatField`?
> - Why does the transfer table need a unique column besides `id`?
> - What does `on_delete` do on your foreign keys, and why did you choose that option?

---

## Phase 3: Wise client (service layer)

No UI in this phase. Everything is tested from tests and the Django shell.

### Step 3.1: Design the client on paper

- **Goal:** know every function's job before writing any of them.
- **Read first:** the API reference page for each endpoint you used in Postman (section 15).
- **Do:** in R&D note `0xx-wise-client-design.md`, write a table with one row per Wise call from Step 0.6:

  | Function (your name) | Wise endpoint | Inputs | What it returns | Errors it can raise |
  |---|---|---|---|---|

  Then decide:
  - Where do the base URL, API version and token come from? (Hint: not hardcoded.)
  - What **timeout** will every request use? What happens with no timeout?
  - What is your **own error type**, so views never see raw `requests` errors?
  - How do you turn JSON numbers into `Decimal` instead of `float`? (Hint: read about the `parse_float` option in Python's `json` module.)
  - Will you send the optional `X-External-Correlation-Id` header? How could it help your API activity log (see dashboard R&D)? Wise only echoes it back; the ID Wise support asks for is the `x-trace-id` response header, so log that too ([rnd/009](rnd/009-errors.md)).
  - How do you make sure the token **never** appears in logs or error messages?
- **Done when:**
  - [ ] Design reviewed by Claude.

### Step 3.2: Build each function test-first

Repeat this loop for every function, in the same order as the Postman flow (profiles → balances → quote → requirements → recipient → patch quote → transfer requirements → transfer → fund → simulate → get transfer).

```text
1. POSTMAN   – the call already works by hand
2. FIXTURE   – save the real response JSON (token-free) as a test file
3. TEST      – write a test that fakes the HTTP call with `responses`
               and asserts what YOUR function returns
4. RED       – run it, watch it fail
5. CODE      – write the function until the test passes
6. REAL      – call it for real against the sandbox from `python manage.py shell`
7. COMMIT
```

- **Read first:**
  - [Django testing](https://docs.djangoproject.com/en/stable/topics/testing/)
  - [pytest-django](https://pytest-django.readthedocs.io/en/latest/)
  - [responses](https://github.com/getsentry/responses)
- **Also test the unhappy paths:** for each function, add at least one test for an error response you recorded in Step 0.6 (e.g. 401, 422).
- **Done when:**
  - [ ] Every function has a passing test.
  - [ ] Every function works for real in the shell.

### Step 3.3: Connect the client to your database

- **Goal:** a function that **calls Wise and records the result**, in a safe order.
- **Read first:** [Database transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)
- **Do:** for "create transfer", write the steps in plain English *before* writing code. Answer these in your notes:
  - What gets saved **before** calling Wise? (Hint: `customerTransactionId`.)
  - What gets saved **after**?
  - What does the row look like if the call fails halfway?
  - What happens on retry?
- **Test before moving on:** fake a Wise timeout in a test. Check what is in your database afterwards, and that a retry doesn't create a duplicate.
- **Done when:**
  - [ ] Failure-order tests pass.

### Step 3.4: Smoke-test command

- **Goal:** one terminal command proves that "I can connect to the Wise sandbox".
- **Read first:** [Custom management commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- **Do:** write a management command that runs the happy path (profiles → balance → quote → recipient → transfer → fund → simulate) and prints each step's result.
- **Done when:**
  - [ ] One command takes a brand-new transfer to `outgoing_payment_sent`, and you can see it in the admin.

> **Phase 3 gate:** Claude reviews the client module, the tests, and the failure-order logic.

---

## Phase 4: Dashboard pages

Page designs and the reasons behind them are in [02-dashboard-rnd.md](02-dashboard-rnd.md). Build the pages in this order. Each page is only a thin layer over the Phase 3 functions.

- **Read first:**
  - [URLs](https://docs.djangoproject.com/en/stable/topics/http/urls/)
  - [Views](https://docs.djangoproject.com/en/stable/topics/http/views/)
  - [Class-based views](https://docs.djangoproject.com/en/stable/topics/class-based-views/)
  - [Templates](https://docs.djangoproject.com/en/stable/ref/templates/language/)
  - [Forms](https://docs.djangoproject.com/en/stable/topics/forms/)
  - [Messages](https://docs.djangoproject.com/en/stable/ref/contrib/messages/)
  - [Auth / login required](https://docs.djangoproject.com/en/stable/topics/auth/default/)
  - [CSRF](https://docs.djangoproject.com/en/stable/ref/csrf/)
  - [Bootstrap 5.3](https://getbootstrap.com/docs/5.3/getting-started/introduction/)

| Step | Page | Test before moving on |
|---|---|---|
| 4.1 | Base layout + login/logout | Logged-out users are redirected to login from every page |
| 4.2 | Overview (connection card, balances, recent transfers) | Shows real sandbox balances. Shows a friendly error (not a crash) when the token is wrong |
| 4.3 | Transfers list | Shows rows from **your DB** with friendly status labels |
| 4.4 | Transfer detail + status timeline + "Refresh status" | Refresh pulls the live status from Wise and updates your DB |
| 4.5 | Send money wizard: quote → recipient → review → create → fund | A full transfer can be created from the browser. Bad input (negative amount, unsupported currency, empty IBAN) is rejected with a clear message |
| 4.6 | Sandbox panel on the detail page (simulate next status, top up balance) | Only the *valid next* simulation button is enabled. The panel is hidden when not in sandbox |
| 4.7 | API activity log page | Every Wise call made from the dashboard appears there with no token visible |

- **Done when:**
  - [ ] You can demo the full flow from the browser without touching Postman.

> **Phase 4 gate questions:**
> - Why is the API call in the service layer and not in the view?
> - What protects the "Fund" button from being double-clicked into two payments?

---

## Phase 5: Keeping statuses up to date

### Step 5.1: Polling (required)

- **Goal:** statuses update without webhooks.
- **Do:**
  1. A management command that refreshes every transfer that isn't in a final status. Careful: `cancelled` is final only if the transfer was never funded, and `outgoing_payment_sent` can still bounce back weeks later ([rnd/006](rnd/006-transfer-statuses.md)).
  2. The "Refresh status" button you already built.
- **Test before moving on:** move a transfer forward with the simulation API, run the command, and check that your DB and the page show the new status.
- **Done when:**
  - [ ] Non-final transfers update by command and by button.

### Step 5.2: Webhooks (stretch goal)

- **Goal:** Wise tells you about changes instead of you asking.
- **Read first:**
  - [Webhooks](https://docs.wise.com/guides/developer/webhooks)
  - [Subscribe to webhooks](https://docs.wise.com/guides/developer/webhooks/subscribe-to-webhooks)
  - [Event handling and signatures](https://docs.wise.com/guides/developer/webhooks/event-handling)
  - [Event ordering](https://docs.wise.com/guides/developer/webhooks/event-ordering)
  - [Essential webhooks](https://docs.wise.com/guides/developer/webhooks/essential-webhooks)
  - [Signature examples (GitHub)](https://github.com/transferwise/digital-signatures-examples/tree/main/verify-webhook-signature)
  - [cryptography: RSA verify](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/)
  - [ngrok](https://ngrok.com/docs/getting-started/)
- **Facts from the docs:**
  - Wise only calls **HTTPS on port 443 with a real domain name**. Use ngrok to expose your laptop.
  - Your endpoint must reply within **5 seconds**, or Wise retries. The pages disagree on "2xx" vs "200", so reply exactly **200**.
  - Every request is signed. Verify the `X-Signature-SHA256` header with the **sandbox public key** from the event-handling page. Wise's examples use **PKCS#1 v1.5 + SHA-256** padding; the `cryptography` page's example shows PSS, which is not what Wise uses.
  - Django's CSRF check answers `403` to Wise's POST, and Wise gives up after three tries on a 403. The webhook view must be exempt from CSRF (read the CSRF docs).
  - `X-Delivery-Id` is unique per delivery *attempt*: a manual retry gets a new ID. Log it, but ignore duplicates by transfer ID + `current_state` + `occurred_at` ([rnd/011](rnd/011-webhooks-vs-polling.md)).
  - Events can arrive **out of order**. Use the event's `occurred_at`, not arrival order.
  - The event to start with is `transfers#state-change`.
- **Experiment first:**
  - Developer Hub (application-level) webhooks need partner access.
  - Test whether your personal token can create a **profile-level** subscription (`POST /profiles/{profileId}/subscriptions`). Wise's SMB payouts guide tells personal-token users to do this, but the API reference lists only OAuth user tokens.
  - If it can't, record that and stay with polling. That's fine for this project.
- **Do (in plain English):**
  1. Receive the request.
  2. Verify the signature.
  3. Reject it if the signature is invalid.
  4. Store the raw event.
  5. Reply 200.
  6. Process the event (update the transfer) separately.
- **Test before moving on:**
  - A forged request (wrong signature) is rejected.
  - The same delivery sent twice changes nothing the second time.
  - A simulated status change shows up on the dashboard without pressing Refresh.
- **Done when:**
  - [ ] Webhooks work end to end, or there's an R&D note explaining why you stayed with polling.

---

## Phase 6: Hardening and demo

| Check | How to verify |
|---|---|
| No secrets in Git | `git log -p` and search for your token/password: nothing found |
| Token never logged | Trigger an error and read the log output |
| Friendly errors | Wrong token, Wise down (fake it in a test), expired quote: each shows a clear message |
| `DEBUG` off works | Run with `DEBUG=False` and check the error pages |
| Logging | [Django logging](https://docs.djangoproject.com/en/stable/topics/logging/) is configured for your Wise client |
| All tests pass | Run the test suite |
| README | A new person can set it up from your README alone (ask a friend to try) |
| Demo script | `docs/demo.md`: the clicks to show, the expected result at each step, and screenshots |

- **Done when:**
  - [ ] Demo runs start to finish in under 5 minutes.

---

## Phase 7: Stripe (future)

### What's different

| | Wise | Stripe |
|---|---|---|
| Direction | Money **out** (payouts) | Money **in** (customer pays you) |
| Main objects | Quote, Recipient, Transfer | PaymentIntent, Checkout Session, Customer |
| Test mode | Separate sandbox site and API URL | Same API, **test keys** (`sk_test_...`) |
| Status updates | Polling or webhooks | Webhooks (strongly recommended) |
| Duplicate protection | `customerTransactionId` (transfers only). Balances use the `X-idempotence-uuid` header; funding has no key, and a second payment gets `409` `payment.exists` | `Idempotency-Key` header |
| Local webhook testing | ngrok | Stripe CLI `stripe listen` |

### Steps (when you get there)

1. **R&D:**
   - [Stripe API](https://docs.stripe.com/api)
   - [API keys](https://docs.stripe.com/keys)
   - [Accept a payment](https://docs.stripe.com/payments/accept-a-payment)
   - [Checkout](https://docs.stripe.com/payments/checkout)
   - [PaymentIntents](https://docs.stripe.com/payments/payment-intents)
   - [Testing (test cards)](https://docs.stripe.com/testing)
   - [Webhooks](https://docs.stripe.com/webhooks)
   - [Stripe CLI](https://docs.stripe.com/stripe-cli)
   - [Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
2. **Postman first:** create a PaymentIntent in test mode by hand.
3. **Design check:** does your Phase 2 schema hold a Stripe payment without renaming anything? If not, write down what you'd change and why.
4. **New client module** for Stripe, next to the Wise one, built with the same test-first loop.
5. **Dashboard:** add a "Receive payment" page and a **provider** filter on the transactions list.

- **Done when:**
  - [ ] A test-mode card payment appears on your dashboard next to the Wise transfers.

> **The real test of your design:** if Phase 2 and 3 were done well, Stripe is *new code next to the old code*, not a rewrite.

---

## 14. Testing strategy

```text
            ▲  slow, few
            │   Manual demo in browser           (Phase 4/6)
            │   Real sandbox calls in the shell  (Phase 3, step 6 of each loop)
            │   Unit tests with faked HTTP       (Phase 3+, run on every change)
            │   Manual Postman calls             (Phase 0, before any code)
            ▼  fast, many
```

- **Unit tests never call the real Wise API.** They use saved fixtures and `responses`.
- **Real sandbox calls** are made by you, on purpose, from the shell or the smoke-test command.
- **One test per behaviour.** Test what *your* code does (what it returns, saves or raises), not what Django or Wise does.

---

## 15. Documentation index

### Wise: guides
| Topic | Link |
|---|---|
| Environments (sandbox/production URLs) | https://docs.wise.com/guides/developer/environments |
| Sandbox V2 migration | https://docs.wise.com/guides/developer/environments/sandbox-v2-migration |
| Global versioning (`2026Q4`) | https://docs.wise.com/guides/developer/global-versioning |
| Personal API token | https://docs.wise.com/guides/developer/auth-and-security/personal-api-token |
| Auth and security overview | https://docs.wise.com/guides/developer/auth-and-security |
| About profiles | https://docs.wise.com/guides/product/account-setup/about-profiles |
| Balance accounts | https://docs.wise.com/guides/product/accounts/balance-accounts |
| Send money overview | https://docs.wise.com/guides/product/send-money |
| Quotes | https://docs.wise.com/guides/product/send-money/quotes |
| Recipients | https://docs.wise.com/guides/product/send-money/recipients |
| Account requirements (dynamic forms) | https://docs.wise.com/api-reference/recipient/recipientaccountrequirementsget |
| Transfers | https://docs.wise.com/guides/product/send-money/transfers |
| Standard transfers | https://docs.wise.com/guides/product/send-money/standard-api-transfers |
| Funding | https://docs.wise.com/guides/product/send-money/funding |
| Fund from balance | https://docs.wise.com/guides/product/send-money/funding/fund-from-balance |
| Transfer statuses | https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses |
| Errors | https://docs.wise.com/guides/developer/errors |
| Webhooks | https://docs.wise.com/guides/developer/webhooks |
| Subscribe to webhooks | https://docs.wise.com/guides/developer/webhooks/subscribe-to-webhooks |
| Event handling and signatures | https://docs.wise.com/guides/developer/webhooks/event-handling |
| Event ordering | https://docs.wise.com/guides/developer/webhooks/event-ordering |
| Essential webhooks | https://docs.wise.com/guides/developer/webhooks/essential-webhooks |
| Signature examples (GitHub) | https://github.com/transferwise/digital-signatures-examples/tree/main/verify-webhook-signature |
| Postman collection: Send money | https://elements.getpostman.com/view/fork?collection=24215266-639bb28a-dbc1-45e6-aca1-e58a86db34a3&workspaceId=a247415a-a90f-4b3c-88d2-14aa27592db4 |
| Sandbox web UI | https://wise-sandbox.com |
| Help: tracking a transfer (consumer view) | https://wise.com/help/articles/2977947/how-do-i-track-my-transfer |

### Wise: API reference
| Resource | Link |
|---|---|
| API reference home | https://docs.wise.com/api-reference |
| Profile | https://docs.wise.com/api-reference/profile |
| Balance | https://docs.wise.com/api-reference/balance |
| Rate | https://docs.wise.com/api-reference/rate |
| Quote | https://docs.wise.com/api-reference/quote |
| Recipient | https://docs.wise.com/api-reference/recipient |
| Transfer | https://docs.wise.com/api-reference/transfer |
| Simulation | https://docs.wise.com/api-reference/simulation |
| Simulate transfer state change | https://docs.wise.com/api-reference/simulation/simulationtransferstatechange |
| Simulate balance top-up | https://docs.wise.com/api-reference/simulation/simulationbalancetopup |
| Webhook subscriptions | https://docs.wise.com/api-reference/webhook |

### Django
| Topic | Link |
|---|---|
| Tutorial (parts 1–7) | https://docs.djangoproject.com/en/stable/intro/tutorial01/ |
| Settings | https://docs.djangoproject.com/en/stable/topics/settings/ |
| Databases / PostgreSQL notes | https://docs.djangoproject.com/en/stable/ref/databases/ |
| Models | https://docs.djangoproject.com/en/stable/topics/db/models/ |
| Model field reference | https://docs.djangoproject.com/en/stable/ref/models/fields/ |
| Migrations | https://docs.djangoproject.com/en/stable/topics/migrations/ |
| Transactions | https://docs.djangoproject.com/en/stable/topics/db/transactions/ |
| `manage.py` commands (`sqlmigrate`, `shell`) | https://docs.djangoproject.com/en/stable/ref/django-admin/ |
| Custom management commands | https://docs.djangoproject.com/en/stable/howto/custom-management-commands/ |
| Admin | https://docs.djangoproject.com/en/stable/ref/contrib/admin/ |
| URLs | https://docs.djangoproject.com/en/stable/topics/http/urls/ |
| Views | https://docs.djangoproject.com/en/stable/topics/http/views/ |
| Class-based views | https://docs.djangoproject.com/en/stable/topics/class-based-views/ |
| Templates | https://docs.djangoproject.com/en/stable/ref/templates/language/ |
| Forms | https://docs.djangoproject.com/en/stable/topics/forms/ |
| Messages | https://docs.djangoproject.com/en/stable/ref/contrib/messages/ |
| Authentication | https://docs.djangoproject.com/en/stable/topics/auth/default/ |
| CSRF | https://docs.djangoproject.com/en/stable/ref/csrf/ |
| Logging | https://docs.djangoproject.com/en/stable/topics/logging/ |
| Testing | https://docs.djangoproject.com/en/stable/topics/testing/ |

### PostgreSQL
| Topic | Link |
|---|---|
| Tutorial | https://www.postgresql.org/docs/current/tutorial.html |
| psql | https://www.postgresql.org/docs/current/app-psql.html |
| CREATE ROLE | https://www.postgresql.org/docs/current/sql-createrole.html |
| CREATE DATABASE | https://www.postgresql.org/docs/current/sql-createdatabase.html |
| GRANT | https://www.postgresql.org/docs/current/sql-grant.html |
| Numeric types | https://www.postgresql.org/docs/current/datatype-numeric.html |
| Constraints | https://www.postgresql.org/docs/current/ddl-constraints.html |
| Indexes | https://www.postgresql.org/docs/current/indexes.html |

### Python and libraries
| Topic | Link |
|---|---|
| `decimal` | https://docs.python.org/3/library/decimal.html |
| `uuid` | https://docs.python.org/3/library/uuid.html |
| `venv` | https://docs.python.org/3/library/venv.html |
| uv projects (init, add, sync) | https://docs.astral.sh/uv/concepts/projects/dependencies/ |
| uv export (`requirements.txt`) | https://docs.astral.sh/uv/concepts/projects/export/ |
| psycopg 3 | https://www.psycopg.org/psycopg3/docs/ |
| django-environ | https://django-environ.readthedocs.io/en/latest/ |
| requests | https://requests.readthedocs.io/en/latest/ |
| responses (mock HTTP) | https://github.com/getsentry/responses |
| pytest-django | https://pytest-django.readthedocs.io/en/latest/ |
| cryptography (RSA verify) | https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/ |

### Tools and concepts
| Topic | Link |
|---|---|
| dbdiagram.io | https://dbdiagram.io |
| Postman download | https://www.postman.com/downloads/ |
| Postman environments | https://learning.postman.com/docs/sending-requests/variables/managing-environments/ |
| Postman guide for this project | [03-postman-guide.md](03-postman-guide.md) |
| R&D notes for this project | [rnd/](rnd/) (001–013) |
| ngrok | https://ngrok.com/docs/getting-started/ |
| Bootstrap 5.3 | https://getbootstrap.com/docs/5.3/getting-started/introduction/ |
| gitignore | https://git-scm.com/docs/gitignore |
| Python .gitignore template | https://github.com/github/gitignore/blob/main/Python.gitignore |
| 12-factor config | https://12factor.net/config |

### Stripe (Phase 7)
| Topic | Link |
|---|---|
| API reference | https://docs.stripe.com/api |
| API keys | https://docs.stripe.com/keys |
| Accept a payment | https://docs.stripe.com/payments/accept-a-payment |
| Checkout | https://docs.stripe.com/payments/checkout |
| PaymentIntents | https://docs.stripe.com/payments/payment-intents |
| Testing | https://docs.stripe.com/testing |
| Webhooks | https://docs.stripe.com/webhooks |
| Stripe CLI | https://docs.stripe.com/stripe-cli |
| Idempotent requests | https://docs.stripe.com/api/idempotent_requests |

---

## 16. Progress log

Fill this in as you go. It becomes your project diary and is useful in your intern review.

| Date | Phase / step | What I did | What I learned | Blockers / questions |
|---|---|---|---|---|
| | 0.1 | | | |
| | | | | |
