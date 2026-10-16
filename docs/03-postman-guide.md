# Postman guide: test the Wise sandbox by hand

| | |
|---|---|
| **Date** | 3 October 2026 |
| **Purpose** | Run the whole Wise send-money flow by hand in Postman, safely, before any Django code exists |
| **Postman version** | Postman docs "Latest (v12)", read on 3 October 2026 |
| **Feeds into** | Roadmap Step 0.6 ([01-project-roadmap.md](01-project-roadmap.md)) and the **Experiment** section of each note in [rnd/](rnd/) |

**How to use this guide**

- Do one section, then go to the next. Do not skip section 3 (the token). **Bold words** are labels you see in Postman. Each section ends with one **Remember** line.
- Every Wise fact comes from the notes in [rnd/](rnd/). "rnd/005" means `docs/rnd/005-funding.md`. Every Postman fact comes from the Postman docs listed in section 13. "[P5]" means source P5.
- **Unverified** means the docs do not say, or they disagree. Your experiment decides. Write down what really happened.
- Two roadmap rules (roadmap section 5) guide this work:
  - **Rule 1:** never write Python for an API call you haven't made by hand in Postman first.
  - **Rule 5:** never paste a real token into notes, screenshots, chat or Git. In this guide the token is always `<your-token>`.

---

## 1. What you will build

```text
Environment  "Wise Sandbox"              URL, version, token (secure), IDs
Collection   "Wise Sandbox – Step 0.6"   auth + one tiny log script
  ├─ A Check token    requests 1, 1a, 1b
  ├─ B Money in       requests 2, 3, 4
  ├─ C Send money     requests 5, 6, 7, 8, 8b, 9, 10
  ├─ D Simulate       requests 11, 12, 13, 14
  └─ E Break it       copies for the 7 experiments (section 9)
```

- Numbers 1–14 are the rows of the roadmap Step 0.6 table. New: **1a** and **1b** check what your token may do. **8b** is transfer requirements. Wise puts it between the quote PATCH and `POST /transfers` (rnd/003, roadmap correction).
- Optional: compare your work with Wise's official collection [W1]. Build your own anyway (roadmap Step 0.6). Wise's older GitHub collection uses retired hosts and `/v1` paths (rnd/005, rnd/007). Never copy those.

> **Remember:** values live in the environment; requests, auth and scripts live in the collection.

## 2. Install Postman and sign in

1. Download the desktop app from <https://www.postman.com/downloads/>. On a Mac you can also run `brew install --cask postman`. When asked, move Postman to the **Applications** folder [P1].
2. Use the desktop app, not the web app. In the web app with Safari, local vault secrets are deleted after seven days of inactivity [P14].
3. Open Postman and sign in, or create a free account. You must be signed in to create a collection [P3]. Without sign-in you only get the "lightweight API Client" [P2].
4. Work in a workspace that only you can see. Never put this collection in a public workspace.

> **Remember:** desktop app, signed in, private workspace.

## 3. Keep the token safe

Postman v12 changed how values are stored. Old tutorials talk about "initial value" and "current value". Those are gone. Now each variable has **one local value**, and sharing is a separate action [P6].

| Where a value can live | Sent to the Postman cloud? | Use in this project |
|---|---|---|
| Variable value (the default) | No: "never synced to the Postman cloud" [P9] | URL, version, IDs |
| Shared value (after you click **Share**) | Yes [P7] | Nothing. Never click **Share** |
| **Secure** variable | No. Stored locally, encrypted (AES, 256-bit key), needs your vault key [P6] | `token` |
| Postman **Local Vault** secret | No. Only this app on this machine [P10] | The token itself |
| Postman Shared Vault | Yes (Solo, Team and Enterprise plans) [P10] | Nothing |

**Put the token in the Local Vault (once)**

1. Click **Vault** in the footer, then **Local Vault** [P11].
2. The first time, Postman makes a **vault key**. Save it in your password manager. By default Postman also saves it to the Mac Keychain [P11]. Click **Open Vault**.
3. In an empty row, enter [P12]:
   - **Key:** `wise-sandbox-token`
   - **Value:** paste the token from your password manager.
   - **Allowed domains:** `api.wise-sandbox.com`. The secret then works only for that host [P12].
4. **Unverified:** P12 says a secret with allowed domains "can only be used at the request level". If the collection auth (section 5) shows the token as unresolved, clear **Allowed domains** and tell Claude.

**Where the token must never go**

- Notes, screenshots, chat, Git (Rule 5), or a URL (rnd/002).
- The **Token** field as plain text. It would be saved in the collection and in the export. Always type `{{token}}`.
- A terminal command, even `grep`. The shell keeps a history.

If you sign out, switch to the web app or use another machine, your local vault secrets are lost. The vault key cannot bring them back [P11]. Paste the token again from your password manager. If the token may have leaked, revoke it in the sandbox web UI and make a new one (rnd/002).

> **Remember:** the token lives in two places only: your password manager and your Postman Local Vault.

## 4. Create the environment

1. In the sidebar, click the add icon and select **Environments** [P8]. Name it `Wise Sandbox`.
2. Add the variables from the table below. Changes save automatically [P8].
3. For `token`: click **Secure** next to the name. Then click the value cell and select the vault secret `wise-sandbox-token` [P13].
4. Select `Wise Sandbox` in the environment selector (top right). Requests use only the active environment [P8].
5. Do not create global or collection variables with the same names. If a name exists in two scopes, Postman uses the narrowest one [P5]. That gets confusing.

| Variable | Value at the start | Filled by | Note |
|---|---|---|---|
| `base_url` | `https://api.wise-sandbox.com` | you | Never a `*.transferwise.tech` or `*.wise.tech` host (rnd/001) |
| `api_version` | `2026Q4` | you | Goes right after the host (rnd/001) |
| `token` | vault secret `wise-sandbox-token` | you, once | **Secure** |
| `profile_id` | empty | script, request 1 | Your BUSINESS profile (rnd/002) |
| `balance_id` | empty | script, request 2 or 3 | Your GBP balance (rnd/005) |
| `balance_idempotence_uuid` | empty | script, request 3 | For the `X-idempotence-uuid` header (rnd/004) |
| `quote_id` | empty | script, request 5 | UUID text (rnd/003) |
| `recipient_id` | empty | script, request 7 | Integer (rnd/003) |
| `customer_transaction_id` | empty | script, request 9 | rnd/004 calls it `ctid` |
| `transfer_id` | empty | script, request 9 | Integer (rnd/003) |

To see the values while you work, click **Variables** at the top right of the workbench [P8].

> **Remember:** a value is local by default. Keep it local: never click **Share**.

## 5. Create the collection

1. In the sidebar, click the add icon and select **Collection** [P3]. Name it `Wise Sandbox – Step 0.6`.
2. Add the five folders A–E: click **View more actions** next to the collection, then **Add folder** [P4].
3. Open the collection's **Authorization** tab. Set **Auth Type** to **Bearer Token**. In **Token**, type `{{token}}` [P16]. Postman then sends `Authorization: Bearer <value>` [P16].
   - Alternative: type `{{vault:wise-sandbox-token}}` instead. Postman supports direct references to Local Vault secrets [P13]. This guide uses `{{token}}` so it matches the roadmap's variable table.
4. In each request's **Authorization** tab, check that it says **Inherit auth from parent** [P15].
5. Open the collection's **Scripts > Post-response** tab and paste this one line. It runs after every request in the collection [P3][P19]:

   ```js
   console.log(pm.response.code, "x-trace-id:", pm.response.headers.get("x-trace-id"));
   ```

   `x-trace-id` is what Wise support asks for (rnd/009). It uses `pm.response.headers.get()` [P22][P23].

**Bodies.** In the **Body** tab, select **raw** and then **JSON** [P17]. Put quotes around text, not around numbers: `"quoteUuid": "{{quote_id}}"` but `"targetAccount": {{recipient_id}}`. Postman replaces each `{{name}}` with its value before sending [P5].

> **Remember:** set auth once, on the collection; every request inherits it.

## 6. Save IDs automatically with tiny scripts

Each request has a **Scripts** tab with **Pre-request** (runs before sending) and **Post-response** (runs after the response) [P19][P20]. You need only these:

| Code | What it does | Source |
|---|---|---|
| `pm.response.json()` | Reads the response body as an object | [P23] |
| `pm.response.code` | The HTTP status code | [P23] |
| `pm.environment.set("name", value)` / `.get("name")` | Saves / reads a value in the active environment | [P24] |
| `pm.test("name", () => { ... })` | A check. The result shows in the **Test Results** tab | [P21] |

- Three lines at most. Scripts are tooling, not project code. You write the real logic later, in Python.
- Save an ID only on success: `if (pm.response.code < 300) ...`. Otherwise an error would overwrite a good ID.

**UUIDs and the retry trap.** `{{$guid}}` gives "a uuid-v4 style guid". `{{$randomUUID}}` gives "a random 36-character UUID" [P25]. **Both make a new value on every send.** So never put `{{$guid}}` straight into the transfer body. A retry would then send a new `customerTransactionId`, and Wise would create a second transfer (rnd/004). Instead, make the ID once, store it, and reuse it:

```js
if (!pm.environment.get("customer_transaction_id")) {
  pm.environment.set("customer_transaction_id", pm.variables.replaceIn("{{$guid}}"));
}
```

`pm.variables.replaceIn()` is how a script uses a dynamic variable [P24][P25]. rnd/004 also shows a terminal way: `python3 -c "import uuid; print(uuid.uuid4())"`.

> **Remember:** a dynamic variable is new on every send. Store the ID once; reuse it on retries.

## 7. The requests, in order

For every request:

- `…` stands for `{{base_url}}/{{api_version}}`, which becomes `https://api.wise-sandbox.com/2026Q4`.
- Auth is inherited from the collection (`Authorization: Bearer <your-token>`). Only extra headers are listed.
- "Save" is the post-response script. "Records into" is the note and Experiment step where you paste the result. Examples come from the docs, as quoted in the notes: they are **not from your account**.

### 7.1 Folder A: check the token first

The 2026Q4 reference lists only `UserToken` (OAuth) for create quote, update quote, account requirements, recipients and the simulations. The guides say a personal token may create quotes and recipients. **Unverified:** which one is right for your token (rnd/002, rnd/007, rnd/008). So test it before you build anything.

| Request | Tests | If you get 401 or 403 |
|---|---|---|
| 1 List profiles | The token works at all | See section 12 |
| 1a Create a quote (probe) | Quote endpoints | **Stop.** Record in rnd/002 step 6. Tell Claude |
| 1b List recipients (probe) | Recipient endpoints | **Stop.** Same |
| 4 Top up (folder B) | Simulation endpoints | **Stop.** Record in rnd/007 step 1. Tell Claude (rnd/007, decision 9) |

Requests 6, 7 and 8 carry the same risk. Write down the status code of each in rnd/002 step 6.

**1. List profiles**: `GET …/profiles` (see rnd/001, rnd/002)

- Save:
  ```js
  const biz = pm.response.json().find(p => p.type === "BUSINESS");
  if (biz) pm.environment.set("profile_id", biz.id);
  ```
- Check: `200`. Expect at least two profiles, `PERSONAL` and `BUSINESS`. Copy only `id`, `type` and `address.countryIso2Code`. Never just take the first item (rnd/002).
- Records into: rnd/001 step 1; rnd/002 step 3.

**1a. Probe: create a quote**: `POST …/profiles/{{profile_id}}/quotes` (see rnd/002)

- Body: the same as request 5. No script: this quote is thrown away. Check the status code only. Records into: rnd/002 step 6.

**1b. Probe: list recipients**: `GET …/accounts?profileId={{profile_id}}&currency=EUR` (see rnd/008)

- Check: the status code, and the top-level shape (is there a `seekPositionForNext`?). Records into: rnd/002 step 6; rnd/008 step 9.

### 7.2 Folder B: money in

**2. List balances**: `GET …/profiles/{{profile_id}}/balances?types=STANDARD` (see rnd/005)

- Save:
  ```js
  const gbp = pm.response.json().find(b => b.currency === "GBP");
  if (gbp) pm.environment.set("balance_id", gbp.id);
  ```
  **Unverified:** the notes do not record the response shape. The script assumes a list of balances with `id` and `currency`. If `balance_id` stays empty, copy it by hand.
- Check: each balance's `id`, `currency` and amount. Records into: rnd/005 step 1.

**3. Create a balance (only if you have no GBP balance)**: `POST …/profiles/{{profile_id}}/balances` (see rnd/004)

- Header: `X-idempotence-uuid: {{balance_idempotence_uuid}}`. It is **required** (rnd/004).
- Pre-request: the section 6 script, with `balance_idempotence_uuid` instead of `customer_transaction_id`.
- Body: **the notes do not record it.** Read "Create a Balance Account" (rnd/004, source S6) and write it yourself.
- Save: `if (pm.response.code < 300) pm.environment.set("balance_id", pm.response.json().id);` (**unverified:** assumes the field is `id`).
- Records into: rnd/004 step 10 (once without the header, then twice with the same UUID).

**4. Top up the balance (sandbox only)**: `POST …/simulation/balance/topup` (see rnd/007, rnd/005)

- Body. `currency` must match the balance (rnd/007):
  ```json
  {"profileId": {{profile_id}}, "balanceId": {{balance_id}}, "currency": "GBP", "amount": 1000}
  ```
- Check: `200` and `"state": "COMPLETED"`. Docs example: `{"transactionId": 5, "state": "COMPLETED", "balancesAfter": [...]}`. On 401 or 403: **stop** (table in 7.1).
- Records into: rnd/007 step 1; rnd/005 step 5.

### 7.3 Folder C: send money

After the quote, you have about 30 minutes to create the transfer (`expirationTime`, rnd/003). Do requests 5 to 9 in one sitting.

**5. Create a quote**: `POST …/profiles/{{profile_id}}/quotes` (see rnd/003)

- Body. Send `sourceAmount` or `targetAmount`, never both (`400 error.quote.amount.onlySingle`):
  ```json
  {"sourceCurrency": "GBP", "targetCurrency": "EUR", "sourceAmount": 100, "targetAccount": null}
  ```
- Save. A new quote starts a new payment, so the old transaction ID is cleared (rnd/004):
  ```js
  if (pm.response.code < 300) pm.environment.set("quote_id", pm.response.json().id);
  pm.environment.set("customer_transaction_id", "");
  ```
- Check: `id`, `rate` (how many decimals? rnd/010), `status`, `expirationTime`, `rateExpirationTime`, `providedAmountType`, `payOut`, and the `paymentOptions` item with `"payIn": "BALANCE"`.
- Records into: rnd/003 steps 1–2; rnd/010 open questions.

**6. Get recipient requirements**: `GET …/quotes/{{quote_id}}/account-requirements` (see rnd/008)

- Header: `Accept-Minor-Version: 1`. It adds the name and email fields (rnd/008).
- Check: every `type`. For `iban`: each `fields[].group[]` item (`key`, `required`, `validationRegexp`, `refreshRequirementsOnChange`). **Unverified:** is the IBAN key `IBAN` or `iban`?
- Records into: rnd/008 steps 2–3; rnd/003 step 3.

**7. Create a recipient**: `POST …/accounts` (see rnd/008, rnd/003)

- Body. The IBAN is Wise's docs example (rnd/008). Use the keys that request 6 gave you. The reference also lists `ownedByCustomer`; check whether you need it.
  ```json
  {"currency": "EUR", "type": "iban", "profile": {{profile_id}},
   "accountHolderName": "Test Recipient", "details": {"iban": "DE89370400440532013000"}}
  ```
- Save: `if (pm.response.code < 300) pm.environment.set("recipient_id", pm.response.json().id);`
- Check: `id`, `type`, `accountSummary` (not masked), `longAccountSummary` (masked?), `displayFields`, and whether `confirmations` exists.
- Records into: rnd/008 step 7; rnd/003 step 4.

**8. Attach the recipient to the quote**: `PATCH …/profiles/{{profile_id}}/quotes/{{quote_id}}` (see rnd/003)

- Header: `Content-Type: application/merge-patch+json`. A `Content-Type` you add yourself wins over the one Postman sets [P17]. In **Headers**, click **hidden** to see what Postman will send [P18].
- Body: `{"targetAccount": {{recipient_id}}}`
- Check: make a before/after table against request 5: `rate`, `payOut`, the BALANCE option's price, `expirationTime`. The price to show is the one from this response (rnd/003).
- Records into: rnd/003 step 5.

**8b. Validate transfer requirements**: `POST …/transfer-requirements` (see rnd/003)

- Body: `{"targetAccount": {{recipient_id}}, "quoteUuid": "{{quote_id}}", "details": {"reference": "R&D 003"}}`
- Check: the field names it returns. Wise says to always call it (rnd/003). Records into: rnd/003 step 6.

**9. Create the transfer**: `POST …/transfers` (see rnd/003, rnd/004)

- Pre-request: the section 6 script (makes `customer_transaction_id` once).
- Body. Never add `sourceAccount`. Use `quoteUuid`, not `quote` (rnd/003):
  ```json
  {"targetAccount": {{recipient_id}}, "quoteUuid": "{{quote_id}}",
   "customerTransactionId": "{{customer_transaction_id}}", "details": {"reference": "R&D 003"}}
  ```
- Save: `if (pm.response.code < 300) pm.environment.set("transfer_id", pm.response.json().id);`
- Check: `id`, `status` (expect `incoming_payment_waiting`), `quoteUuid`, `rate`, `sourceValue`, `targetValue`. Optional: `GET …/profiles/{{profile_id}}/quotes/{{quote_id}}` and note its `status` (rnd/003 step 8).
- Records into: rnd/003 step 7; rnd/004 step 2.

**10. Fund the transfer from the balance**: `POST …/profiles/{{profile_id}}/transfers/{{transfer_id}}/payments` (see rnd/005, rnd/002)

- Body: `{"type": "BALANCE"}`
- Post-response test. **Decide from the body, never from the HTTP code alone:** a `REJECTED` body can come with HTTP `201` (rnd/005).
  ```js
  pm.test("Funding COMPLETED", () => pm.expect(pm.response.json().status).to.eql("COMPLETED"));
  ```
- Check: body `status` (`COMPLETED`, or `REJECTED` with an `errorCode`). Headers `x-2fa-approval` and `x-2fa-approval-result`: present, yes or no only. `x-trace-id`. Then send request 14 at once and note the `status` (Experiment E5).
- **A `403` with `x-2fa-approval` means SCA.** Do not retry in a loop. Fund this same transfer in the sandbox web UI (`https://wise-sandbox.com`, 2FA code `111111`). Then continue with request 11 by API (rnd/002 step 8).
- **Unverified (Experiment E2):** whether a UK sandbox profile gets this 403. Also whether the rule "personal-token API funding only for US, CA, AU, NZ, SG, MY" applies in the sandbox (rnd/002, rnd/005).
- Records into: rnd/002 step 7; rnd/005 steps 3–7.

### 7.4 Folder D: simulate and check

Rules (rnd/007): fund first. Call in order. Call `/processing` even if the status already says `processing`. **Wait at least 5 seconds between calls**: the reply is fast, but the processing behind it is not.

| # | Request | Allowed from |
|---|---|---|
| 11 | `GET …/simulation/transfers/{{transfer_id}}/processing` | `incoming_payment_waiting` (funded) |
| 12 | Wait 5 s, then `GET …/simulation/transfers/{{transfer_id}}/funds_converted` | `processing` |
| 13 | Wait 5 s, then `GET …/simulation/transfers/{{transfer_id}}/outgoing_payment_sent` | `funds_converted` |
| 14 | `GET …/transfers/{{transfer_id}}` | Expect `outgoing_payment_sent` |

- No body. Optional test for 11–13: `pm.test("200", () => pm.response.to.have.status(200));` [P21]
- Check: the code and `status` after each call, then request 14. The docs list only `200` and `429` for this endpoint (rnd/007).
- Optional unhappy path: `bounced_back`, then `funds_refunded`, 5 s apart (rnd/007 step 7).
- Records into: rnd/007 steps 3–7; rnd/006 step 1; rnd/011 part A steps 1–2.

> **Remember:** each request hands one ID to the next: quote → recipient → transfer. `profile_id` is in almost every call (rnd/003).

## 8. Simulations: wait by hand, or let the Runner wait

**Option A, by hand.** Send 11. Look at the clock. Wait at least 5 seconds. Send 12. Wait. Send 13. Then send 14.

**Option B, Collection Runner** [P27]:

1. Click **Items** in the sidebar, then **Collections**. Select folder **D Simulate** and click **Run**.
2. Under **Run type**, select **Functional**, then **Local**. A local run uses your local values, including the token. Cloud runs can use only shared values [P5][P14], so they cannot see your token.
3. Check that `Wise Sandbox` is the active environment.
4. Set **Delay** to `6000`. It is a delay before each request, in milliseconds [P27]. Six seconds gives a small margin over five.
5. Leave **Iterations** at `1`. Click **Start run**. Read each status code and response in the results [P27].

- Run folder D only after request 10 says `COMPLETED`, or after you funded in the web UI.
- Never run folder C with more than one iteration. Each iteration would create a new transfer.
- If a run's scripts save IDs, tick **Keep variable values**. Without it, the changes are not kept after the run [P27].

> **Remember:** fund first, then simulate, with at least 5 seconds between calls.

## 9. The seven "break it" experiments

Make a copy of the request in folder E for each test, so the originals stay clean. A request's own auth setting replaces the inherited one [P15]. "Expect" is what the docs say. Record what really happens.

1. **Wrong token** → rnd/009 steps 1–2; rnd/002 step 5.
   Copy request 1. In its **Authorization** tab, choose **Bearer Token** and type `wrong-token`. Never edit your real token. Make a second copy with **No Auth** [P16]. Expect `401`. No token gave `401 missing_token` in rnd/001. The docs show `invalid_token` for a bad token; the sandbox body is **unverified**.
2. **Expired or invalid quote ID** → rnd/003 step 10; rnd/009 steps 4–5.
   (a) Copy request 6 with the URL `…/quotes/not-a-real-id/account-requirements`. (b) Make a new quote. Wait until after its `expirationTime` (about 30 minutes). Then send 8 and 9 with it. Expect PATCH `422 error.quote.expired` and transfer `400 error.quote.expired`.
3. **Bad IBAN** → rnd/008 step 8; rnd/009 step 6.
   Copy request 7 with `"iban": "DE00"`. Read `errors[].path`. **Unverified:** `400` or `422`.
4. **Duplicate `customerTransactionId`** → rnd/004 steps 1–9; rnd/009 step 8.
   Make a fresh quote (5), then 8 and 8b with your existing `recipient_id`. Send 9 (test A). Send it again unchanged (B). Change only `details.reference` and send (C). For D, empty `customer_transaction_id` and send. For E, write down the ID (it is not secret), make and PATCH a new quote, paste the old ID back, and send. **Do not fund.** Then cancel each test transfer: `PUT …/transfers/{transferId}/cancel` (rnd/004 step 9). **Unverified:** what a repeat returns (the same transfer or an error), and whether cancel is `PUT` or `POST`.
5. **Funding with too little balance** → rnd/005 steps 2–9; rnd/009 step 9.
   Make a quote with `sourceAmount` above your GBP balance (for example `5000`). Do 6 to 9, then 10. Expect body `"status": "REJECTED"`; the transfer stays `incoming_payment_waiting`. **Two codes are documented:** `balance.insufficient-funds` and `transfer.insufficient_funds`. Which one the sandbox sends is unverified. Then top up (4) and send 10 again. A third 10 should be refused (`payment.exists`, `409`).
6. **Simulating before funding** → rnd/007 step 2.
   New transfer (5 to 9). Skip 10. Send 11, then 14. Not documented: record exactly what you get.
7. **Simulating two steps with no wait** → rnd/007 step 8.
   On a new funded transfer, send 11 and then 12 at once, by hand. Wait 10 s, then send 14. Not documented.

> **Remember:** the docs tell you what to expect; only your experiment tells you what happens.

## 10. Record results in the rnd notes

1. Open the Console: click **Console** in the footer, or press ⌘+Option+C on a Mac [P26]. Console logs stay on your computer; they are not synced [P26].
2. Send the request. The Console shows the request headers and body, and the raw response [P26]. The collection script (section 5) prints the `x-trace-id`.
3. Paste into the note's **Experiment** section, under the step number, like this:

   ```text
   rnd/005 step 3 – 3 Oct 2026 14:05
   POST https://api.wise-sandbox.com/2026Q4/profiles/<profile_id>/transfers/<transfer_id>/payments
   Authorization: Bearer <your-token>
   Body: {"type": "BALANCE"}
   → 201   x-trace-id: <value>   x-2fa-approval present: no
   {"type": "BALANCE", "status": "REJECTED", "errorCode": "<value>"}
   ```

4. **Remove the token.** The Console logs the request headers [P26], so the `Authorization` line may show your real token. Vault secrets are masked in the Console by default [P13]. **Unverified:** whether this also hides the header built from a secure variable. Look once. Either way, always write `Bearer <your-token>`.
5. Hide personal data, such as real names (rnd/002). Wise IDs are fine. Screenshots: response bodies only. Never the vault, the environment, the **Authorization** tab, the hidden headers or the Console request headers.
6. Before you save a note, run this from the repo root. It must print nothing:

   ```sh
   grep -rn -i "bearer" docs/rnd/ | grep -v -e "<your-token>" -e "wrong-token"
   ```

> **Remember:** paste `Bearer <your-token>`, never the real header.

## 11. Export the collection to `docs/postman/`

1. Click **Collections** in the sidebar. Next to the collection, click **View more actions**, then **More > Export collection**, then **Export JSON** [P28].
2. Save it as `docs/postman/wise-sandbox.postman_collection.json`. **Do not export the environment.**
3. Format: Postman v11 asked you to choose **Collection v2** or **Collection v2.1** [P29]. The v12 page shows no choice [P28]. v12's own format is schema 3.0.0 (YAML files), and Newman runs "2.1.0" exports [P30]. **Unverified:** which schema the v12 JSON file uses. The first command below shows it; write it down.
4. Check the file for the token. Run from the repo root:

   ```sh
   grep -n '"schema"' docs/postman/*.json
   grep -n -i -A6 '"bearer"' docs/postman/*.json
   grep -n -E '"value": *"[^{"][^"]{24,}"' docs/postman/*.json
   ls docs/postman/
   ```

   - The bearer `value` must be `{{token}}` (or `{{vault:wise-sandbox-token}}`), nothing else.
   - The third command lists long plain values. Read each one. None may be a token.
   - `ls` must show only the collection file.
   - Never type the real token into `grep`. It would stay in your shell history.
5. Add `*.postman_environment.json` to `.gitignore` (Step 0.1 question: is it secret? Yes).
6. `git add` only the collection file. Read `git diff --cached` once more. Then commit.

> **Remember:** export the collection, never the environment, and grep before you commit.

## 12. Troubleshooting

| You see | Likely cause | What to do |
|---|---|---|
| `401` `missing_token` | No auth sent: environment not active, request not on **Inherit auth from parent**, or vault locked | Select the environment. Fix the auth. Open **Local Vault** and enter your vault key [P14] (rnd/001) |
| `401`, another body | Wrong or revoked token, **or** a good token with no access to this `profile_id` | Check `profile_id` and the vault secret. Do not retry in a loop (rnd/009) |
| `403` with `x-2fa-approval` headers | SCA on funding (UK/EEA profile) | Stop. Fund in the sandbox web UI, then continue at request 11 (rnd/002, rnd/005) |
| `403` without those headers | Not allowed. Maybe a personal token on a `UserToken`-only endpoint | Stop. Record the body. Tell Claude (rnd/007) |
| `404` `Resource not found` | `/{{api_version}}` missing from the URL, an empty variable, a wrong ID, or a simulation status not in the list | Read the final URL in the Console [P26]. It must start with `https://api.wise-sandbox.com/2026Q4/` (rnd/001, rnd/007) |
| `410` "no longer available" | An old host such as `api.sandbox.transferwise.tech` | Use `{{base_url}}` only (rnd/001) |
| `400` or `422` | A field or a business rule failed | Read `errors[].path`: it names the field. Expired quote (`422 error.quote.expired`): make a new quote (rnd/009, rnd/003) |
| `429` | Rate limit (personal token: 100 per second, 900 per minute) | Wait the `Retry-After` seconds. Never trigger it on purpose (rnd/009) |
| Funding body `"status": "REJECTED"`, not enough money | `balance.insufficient-funds` or `transfer.insufficient_funds` | Top up (request 4), then fund the **same** transfer again (rnd/005) |
| Funding refused | `balance.unauthorised.missing-security-role`, `balance.payment-option-unavailable` or `transfer.not-accessible-for-user` (maybe the country rule; unverified) | Fund in the web UI, then simulate by API (rnd/002, rnd/005) |
| Funding `409` or `payment.exists` | Already paid | Do not pay again. Check with request 14 (rnd/004, rnd/005) |
| `{{name}}` shown red or empty | Environment not active, empty value, or vault secret unresolved | Click **Variables** (top right) and fix the value [P8][P14] |

## 13. Sources

Postman pages were read in their Markdown form (page URL + `.md`) on 3 October 2026. All show "Latest (v12)" unless marked.

| # | Title | URL | Domain | What it proves |
|---|---|---|---|---|
| P1 | Install Postman | https://learning.postman.com/docs/getting-started/installation/install-app/ | learning.postman.com | Mac download, `brew install --cask postman`, move to Applications |
| P2 | Lightweight Postman API Client | https://learning.postman.com/docs/getting-started/basics/using-api-client/ | learning.postman.com | Without sign-in you get the lightweight client |
| P3 | Create collections of API requests | https://learning.postman.com/docs/use/use-collections/create-collections/ | learning.postman.com | Sign-in needed; collection **Authorization** and **Scripts > Post-response** apply to every request |
| P4 | Manage and organize Postman Collections | https://learning.postman.com/docs/use/use-collections/manage-collections/ | learning.postman.com | **View more actions > Add folder** |
| P5 | Store and reuse values using variables | https://learning.postman.com/docs/use/send-requests/variables/variables/ | learning.postman.com | Scopes, narrowest wins; values local by default; cloud features use shared values |
| P6 | Define variables in Postman | https://learning.postman.com/docs/use/send-requests/variables/define-variables/ | learning.postman.com | **Secure** (AES 256-bit, local, vault key); initial/current values replaced by one local value |
| P7 | Share variables in Postman | https://learning.postman.com/docs/use/send-requests/variables/share-variables/ | learning.postman.com | **Share** syncs a value to the cloud; shared values are published with docs |
| P8 | Group sets of variables using environments | https://learning.postman.com/docs/use/send-requests/variables/managing-environments/ | learning.postman.com | Create an environment; environment selector; local value used when sending; **Variables** pane |
| P9 | Edit and set environment variables | https://learning.postman.com/docs/use/send-requests/variables/environment-variables/ | learning.postman.com | Value "never synced to the Postman cloud"; scripts can set values |
| P10 | Store secrets in Postman Vault | https://learning.postman.com/docs/use/postman-vault/postman-vault-secrets/ | learning.postman.com | Local Vault: not synced, all plans. Shared Vault: cloud, paid plans |
| P11 | Access Postman Vault | https://learning.postman.com/docs/use/postman-vault/postman-vault-key/ | learning.postman.com | Vault key, Keychain, **Open Vault**; secrets lost after sign-out or on a new machine |
| P12 | Create and manage vault secrets | https://learning.postman.com/docs/use/postman-vault/manage-vault-secrets/ | learning.postman.com | **Key**, **Value**, **Allowed domains**; the "request level" limit |
| P13 | Use vault secrets in Postman | https://learning.postman.com/docs/use/postman-vault/use-vault-secrets/ | learning.postman.com | Secure variable holding a vault secret; `{{vault:name}}`; Console masks vault secrets by default |
| P14 | Troubleshoot vault secrets | https://learning.postman.com/docs/use/postman-vault/troubleshoot-vault-secrets/ | learning.postman.com | Unresolved secrets (vault key, allowed domains); Safari web app deletes after 7 days; cloud runs see shared values only |
| P15 | Add API authorization details to requests | https://learning.postman.com/docs/use/send-requests/authorization/specifying-authorization-details/ | learning.postman.com | **Inherit auth from parent**; a request can choose its own auth |
| P16 | Authorization types supported by Postman | https://learning.postman.com/docs/use/send-requests/authorization/authorization-types/ | learning.postman.com | **Bearer Token** sends `Bearer <token>`; **No Auth** |
| P17 | Send parameters and body data | https://learning.postman.com/docs/use/send-requests/create-requests/parameters/ | learning.postman.com | **raw** + **JSON**; a manual `Content-Type` wins |
| P18 | Configure headers for API requests | https://learning.postman.com/docs/use/send-requests/create-requests/headers/ | learning.postman.com | **hidden** shows auto-added headers |
| P19 | Use scripts to add logic and tests | https://learning.postman.com/docs/tests-and-scripts/write-scripts/intro-to-scripts/ | learning.postman.com | **Scripts > Pre-request / Post-response**; collection scripts run for every request |
| P20 | Write pre-request scripts | https://learning.postman.com/docs/tests-and-scripts/write-scripts/pre-request-scripts/ | learning.postman.com | Pre-request code runs before the request is sent |
| P21 | Write scripts to test API response data | https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-scripts/ | learning.postman.com | `pm.test`, `pm.response.to.have.status`, **Test Results** tab |
| P22 | Postman test script examples | https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-examples/ | learning.postman.com | `pm.response.json()`, `pm.response.headers.get()` |
| P23 | Reference Postman responses in scripts | https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-response/ | learning.postman.com | `pm.response.code`, `.headers`, `.json()` |
| P24 | Reference variables in Postman scripts | https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-variables/ | learning.postman.com | `pm.environment.get/set`, `pm.variables.replaceIn` |
| P25 | Use dynamic variables | https://learning.postman.com/docs/tests-and-scripts/write-scripts/variables-list/ | learning.postman.com | `$guid` (uuid-v4), `$randomUUID`; generated when the request runs; `replaceIn` in scripts |
| P26 | Debug API requests in Postman | https://learning.postman.com/docs/use/send-requests/response-data/troubleshooting-api-requests/ | learning.postman.com | Console: footer, ⌘+Option+C, request headers, raw response, stays local |
| P27 | Test your API using the Collection Runner | https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs/ | learning.postman.com | **Run**, **Functional > Local**, **Delay** (ms, before each request), **Keep variable values** |
| P28 | Export data from Postman (v12) | https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/ | learning.postman.com | **More > Export collection > Export JSON**; no format choice |
| P29 | Export data from Postman (v11, older) | https://learning.postman.com/v11/docs/getting-started/importing-and-exporting/exporting-data/ | learning.postman.com | The old **Collection v2** / **v2.1** choice |
| P30 | Postman Collections schemas | https://learning.postman.com/docs/use/use-collections/collections-schemas/ | learning.postman.com | v12 uses schema 3.0.0; Newman runs 2.1.0 exports |
| W1 | Wise "Send money" Postman collection (linked in roadmap Step 0.6) | https://elements.getpostman.com/view/fork?collection=24215266-639bb28a-dbc1-45e6-aca1-e58a86db34a3&workspaceId=a247415a-a90f-4b3c-88d2-14aa27592db4 | elements.getpostman.com | Opened 3 Oct 2026: a fork page; contents not checked. Compare only; take hosts and paths from rnd/001 |
| R | Project roadmap and R&D notes | [01-project-roadmap.md](01-project-roadmap.md); [rnd/001](rnd/001-wise-environments-and-versioning.md), [002](rnd/002-profiles-and-tokens.md), [003](rnd/003-send-money-flow.md), [004](rnd/004-customer-transaction-id.md), [005](rnd/005-funding.md), [006](rnd/006-transfer-statuses.md), [007](rnd/007-simulation.md), [008](rnd/008-recipients-and-account-requirements.md), [009](rnd/009-errors.md), [010](rnd/010-money-as-decimal.md), [011](rnd/011-webhooks-vs-polling.md) | this repo | Every Wise fact in this guide: hosts, `/2026Q4`, paths, headers, bodies, error codes, simulation order, 5-second wait |
