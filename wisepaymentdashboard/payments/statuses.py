"""Provider statuses: one place for labels, badge colours and final states.

Wise labels are Wise's recommended wording (docs/rnd/006-transfer-statuses.md).
Stripe Checkout labels follow docs/rnd/014-stripe-sandbox.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StatusInfo:
    label: str
    badge: str
    group: str
    is_final: bool


STATUSES = {
    "incoming_payment_waiting": StatusInfo("On its way to Wise", "secondary", "Waiting", False),
    "incoming_payment_initiated": StatusInfo("On its way to Wise", "secondary", "Waiting", False),
    "processing": StatusInfo("Processing", "primary", "Processing", False),
    "funds_converted": StatusInfo("Processing", "primary", "Processing", False),
    "outgoing_payment_sent": StatusInfo("Payment sent", "success", "Sent", True),
    "bounced_back": StatusInfo("Bounced back", "warning", "Problem", False),
    "funds_refunded": StatusInfo("Payment refunded", "warning", "Problem", True),
    # Final only if the transfer was never funded; see Transfer.is_final.
    "cancelled": StatusInfo("Payment cancelled", "danger", "Problem", True),
    "charged_back": StatusInfo("Funds returned to sender", "danger", "Problem", False),
    "unknown": StatusInfo("Payment status unknown", "warning", "Problem", False),
    # Our wording: Wise gives no label for this status.
    "waiting_recipient_input_to_proceed": StatusInfo(
        "Waiting for recipient details", "warning", "Problem", False
    ),
}

NOT_SUBMITTED = StatusInfo("Not sent to Wise yet", "light", "Waiting", False)
UNRECOGNISED = StatusInfo("Status not recognised by this app", "dark", "Problem", False)

STATUS_GROUPS = ("Waiting", "Processing", "Sent", "Problem")

# Statuses that prove the money reached Wise.
FUNDED_STATUSES = {"processing", "funds_converted", "outgoing_payment_sent", "bounced_back", "funds_refunded"}

# Sandbox simulations, in the only order Wise accepts them.
SIMULATION_STEPS = ("processing", "funds_converted", "outgoing_payment_sent", "bounced_back", "funds_refunded")


def get_status_info(status: str) -> StatusInfo:
    if not status:
        return NOT_SUBMITTED
    return STATUSES.get(status, UNRECOGNISED)


def get_next_simulation(last_simulated: str) -> str | None:
    if not last_simulated:
        return SIMULATION_STEPS[0]
    index = SIMULATION_STEPS.index(last_simulated) + 1
    return SIMULATION_STEPS[index] if index < len(SIMULATION_STEPS) else None


def get_checkout_status_info(status: str, payment_status: str) -> StatusInfo:
    """Stripe Checkout reports two fields; turn them into one label."""
    if not status:
        return StatusInfo("Not sent to Stripe yet", "light", "Waiting", False)
    if status == "expired":
        return StatusInfo("Expired", "danger", "Problem", True)
    if status == "open":
        return StatusInfo("Waiting for customer", "secondary", "Waiting", False)
    if payment_status in ("paid", "no_payment_required"):
        return StatusInfo("Paid", "success", "Paid", True)
    return StatusInfo("Processing", "primary", "Processing", False)
