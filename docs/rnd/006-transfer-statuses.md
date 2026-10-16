# 006 – Transfer statuses and friendly labels
Date: 3 October 2026
Roadmap step: Step 0.5, Q8 (also Glossary "Transfer status"; 02-dashboard-rnd F2 and 6.4)

## Question
- **Q8:** List every transfer status. Which are **final**? Which friendly label does Wise recommend for each?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Tracking transfers | https://docs.wise.com/guides/product/send-money/tracking/transfer-statuses | docs.wise.com | official doc | 2026-09-04 | Full status table, final states, recommended descriptions, happy and unhappy paths, rollback transitions, bounce timing |
| S2 | Transfer state diagram (image on S1) | https://wise.com/public-resources/assets/api-docs/transfer_state_diagram.svg | wise.com | official doc | accessed 2026-10-03 | Shows `waiting_recipient_input_to_proceed`; does not show `incoming_payment_initiated`; arrows between states |
| S3 | Get transfer by ID | https://docs.wise.com/api-reference/transfer/transferget | docs.wise.com | official doc | accessed 2026-10-03 | `status` is a plain string; "See Tracking transfers for all possible statuses" |
| S4 | OpenAPI file, 2026Q4 | https://docs.wise.com/_bundle/api-reference/@latest/index.json?download | docs.wise.com | official doc | accessed 2026-10-03 | Transfer `status` has no enum; `charged_back` and `waiting_recipient_input_to_proceed` appear nowhere in the file |
| S5 | Transfer state change (webhook event) | https://docs.wise.com/api-reference/transfer/eventtransfersstatechange | docs.wise.com | official doc | accessed 2026-10-03 | Events carry `current_state` and `previous_state`; "Events may not be delivered in the order they occurred" |
| S6 | Transfers (API reference) | https://docs.wise.com/api-reference/transfer | docs.wise.com | official doc | accessed 2026-10-03 | `incoming_payment_initiated` appears in the US combined receipt endpoint; unfunded transfers "usually" cancelled after fourteen days |
| S7 | Cancel a transfer | https://docs.wise.com/api-reference/transfer/transfercancel | docs.wise.com | official doc | accessed 2026-10-03 | Cancel only from `incoming_payment_waiting`; response example `status` `cancelled`; `409` `transfer.cancellation.not.allowed` |
| S8 | Simulate transfer state change | https://docs.wise.com/api-reference/simulation/simulationtransferstatechange | docs.wise.com | official doc | accessed 2026-10-03 | Only five statuses can be simulated |
| S9 | Wise Help Centre: How do I check my transfer's status? | https://wise.com/help/articles/2452305/how-do-i-check-my-transfers-status | wise.com | official doc (help centre) | accessed 2026-10-03 | Wise's own app uses other words ("Money received", "Transfer Sent"); no mapping to API statuses |
| S10 | foss-fund/wise-banking-api-client, `model/transfer.py` | https://github.com/foss-fund/wise-banking-api-client/blob/main/wise_banking_api_client/model/transfer.py | github.com | community GitHub | last commit 2025-01-30, 0 stars | Its status list has 11 values, including `waiting_recipient_input_to_proceed`. **Outdated** elsewhere in the repo (old sandbox host, `/v1` paths) |

## Experiment (request, response, screenshots – token removed)
Status: **Not run yet — needs your sandbox token.**

All paths go after `{{base_url}}/{{api_version}}` (= `https://api.wise-sandbox.com/2026Q4`). Header: `Authorization: Bearer <your-token>`.

1. Run the note 007 experiment. After every simulation call, wait 5+ seconds, then `GET /transfers/{transferId}`. Paste the exact `status` each time, as a list.
2. Right after funding (note 005, step 7), paste `status`. Is it `incoming_payment_waiting`, `incoming_payment_initiated` or `processing`?
3. **Cancel:** create a new transfer, do not fund it, then `PUT /transfers/{transferId}/cancel`. Paste the HTTP code and the `status` in the response. Then `GET /transfers/{transferId}` and paste `status`.
4. **Cancel not allowed:** on a transfer in `funds_converted`, `PUT /transfers/{transferId}/cancel`. Paste code + body.
5. **Unhappy path:** after the `bounced_back` and `funds_refunded` simulations, `GET /transfers/{transferId}` each time. Does `processing` or `cancelled` appear in between? Paste.
6. Open each transfer in the sandbox web UI (`https://wise-sandbox.com`). Screenshot the wording Wise shows at each status.

Example from docs [S7] (cancel response), not from your account: `"status": "cancelled"`.

## Finding (in your own words)
**Wise lists 10 statuses in its main table [S1]. Its diagram adds an 11th, `waiting_recipient_input_to_proceed` [S2].** The labels below are Wise's "consumer-friendly descriptions", quoted exactly [S1].

**Happy path:** `incoming_payment_waiting` → `processing` → `funds_converted` → `outgoing_payment_sent` [S1]

| Status | What it means | Final? | Wise's recommended label | Source |
|---|---|---|---|---|
| `incoming_payment_waiting` | Transfer submitted; Wise waits for the money | No | "On its way to Wise" | S1 |
| `incoming_payment_initiated` | Funding started, money not yet at Wise | No | "On its way to Wise" | S1 |
| `processing` | Wise has the money and runs checks (AML, compliance, fraud) | No | "Processing" | S1 |
| `funds_converted` | Checks done; money converted to the target currency | No | "Processing" | S1 |
| `outgoing_payment_sent` | Wise has sent the money. It does **not** mean it reached the recipient's bank | Yes, "assuming funds will not be returned" | "Payment sent" | S1 |

**Unhappy path:** `outgoing_payment_sent` → `bounced_back` → `processing` → `cancelled` → `funds_refunded` [S1]

| Status | What it means | Final? | Wise's recommended label | Source |
|---|---|---|---|---|
| `bounced_back` | Payment came back; not yet cancelled or refunded. Will be delivered late or go to `funds_refunded` | No | "Bounced back" | S1 |
| `cancelled` | Transfer never funded, never processed | Yes, **for never-funded transfers**. In the unhappy path it is followed by `funds_refunded` | "Payment cancelled" | S1 |
| `funds_refunded` | Money returned to the sender | Yes ("final state of a transfer that was funded and then cancelled") | "Payment refunded" | S1 |
| `charged_back` | Wise could not debit the payer, or the payer asked for the money back. It "can follow from any other transfer status" | Not stated | "Funds returned to sender" | S1 |
| `unknown` | Wise lacks information to reach a final state; Wise emails for more information | No | "Payment status unknown" | S1 |
| `waiting_recipient_input_to_proceed` | Not described in text. In the diagram it sits between `incoming_payment_waiting` and `processing`/`cancelled` | Not stated | **None given** | S2 only |

**Which are final?** `outgoing_payment_sent` (normal end), `cancelled` (never funded) and `funds_refunded` [S1]. Everything else is not final, or the docs do not say.

**Other rules from S1:**
- "Transfers support rollback transitions". A status can go **backwards** (for example `bounced_back` → `processing`).
- "Most bounce backs occur within 2-3 business days. However, they can happen up to several weeks after a transfer is sent."
- "Completed" on Wise's website means `outgoing_payment_sent`. Wise's own app tracker uses yet other words [S9].

**Diagram arrows** (my reading of the image [S2]): `incoming_payment_waiting` → `waiting_recipient_input_to_proceed`, `processing` or `cancelled`. `waiting_recipient_input_to_proceed` → `processing` or `cancelled`. `processing` → `funds_converted` or `cancelled`. `funds_converted` → `outgoing_payment_sent` or `bounced_back`. `outgoing_payment_sent` ⇄ `bounced_back`. `bounced_back` → `processing`. `bounced_back` ⇄ `funds_refunded`. `cancelled` → `funds_refunded`. `charged_back` and `unknown` have no arrows.

**Where the pages disagree:**
- `incoming_payment_initiated`: in the text and labels tables [S1]; **not** in the diagram [S2]. Also mentioned for the US combined receipt [S6].
- `waiting_recipient_input_to_proceed`: **only** in the diagram [S2]. Not in either table [S1], not in the API file [S4]. One community client lists it [S10].
- `charged_back`: in the tables and the diagram, but nowhere in the API file [S4].
- The API reference gives the transfer `status` as a plain string with no fixed list [S3][S4]. New values could appear.

**What the sandbox can produce:** only `processing`, `funds_converted`, `outgoing_payment_sent`, `bounced_back`, `funds_refunded` by simulation [S8]. `cancelled` comes from the cancel call [S7] or the auto-cancel [S6]. There is no documented way to produce `incoming_payment_initiated`, `charged_back`, `unknown` or `waiting_recipient_input_to_proceed` in the sandbox. Note: the simulated unhappy path goes `bounced_back` → `funds_refunded`, skipping the `processing` → `cancelled` steps of the real path [S1][S8].

Roadmap correction: 02-dashboard-rnd F2 and 6.4 list 10 statuses. The diagram on the same Wise page also has `waiting_recipient_input_to_proceed` [S2]. Add it, with a label you choose yourself.

Roadmap correction: 02-dashboard-rnd F2 says `cancelled` is final and means "Never funded". The unhappy path shows `cancelled` → `funds_refunded` for a funded transfer [S1]. `cancelled` is final only when the transfer was never funded.

Roadmap correction: 02-dashboard-rnd F2 says `charged_back` is final "Depends". The docs do not say whether it is final [S1]. Write "not stated".

Roadmap correction: 02-dashboard-rnd 6.4 builds the timeline as "step reached", which assumes statuses only move forward. Wise says rollback transitions exist [S1].

## Decision (what you will do and why)
1. **Store the status as plain text, exactly as Wise sends it.** Do not reject values you don't know. Why: the API field has no fixed list, and the pages disagree [S3][S4].
2. **Keep one mapping table in one place:** status → label, final?, badge colour. Use Wise's labels word for word for the 10 listed statuses. Why: Wise recommends them [S1].
3. **Unrecognised status → show the raw value with your own fallback label** (for example "Status not recognised by this app"). Treat it as not final. Why: Wise's `unknown` already has its own label; don't mix them.
4. **`waiting_recipient_input_to_proceed`: choose your own label and mark it "our wording" in a code comment.** Why: Wise gives none [S2].
5. **Stop automatic polling at `funds_refunded`, at `outgoing_payment_sent`, and at `cancelled` only if the transfer was never funded. Keep the manual "Refresh" button always.** Why: a funded transfer can go `cancelled` → `funds_refunded`, and `outgoing_payment_sent` can still bounce weeks later [S1].
6. **Proposed — confirm after the experiment:** treat `charged_back` as not final and keep polling it. Why: the docs don't say [S1].
7. **Build the timeline from status-history rows in time order, not from "highest step reached".** Why: statuses can roll back [S1], and webhooks can arrive out of order [S5].
8. **Show both the label and the raw status**, as 02-dashboard-rnd already says. Why: users need words; you need the real value for debugging.

## Open questions
- What does `waiting_recipient_input_to_proceed` mean, when does it happen, and is it still used? Only the diagram shows it [S2].
- Is `charged_back` final? Can a transfer leave `unknown`, and to which status?
- When exactly does Wise use `incoming_payment_initiated`? Does the sandbox ever show it (step 2)?
- In the sandbox, does the unhappy path pass through `processing` and `cancelled` (step 5)?
- Does the sandbox web UI use Wise's recommended labels or other words (step 6)?
