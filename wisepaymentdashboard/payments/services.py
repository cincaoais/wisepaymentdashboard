"""Business steps: call the provider, then record the result.

Wise sends money out (quote → recipient → transfer → fund). Stripe takes money in
(hosted Checkout page). Views call these functions; only `payments/providers/`
talks to the providers.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from payments.models import Payment, StatusChange, Transfer
from payments.providers.stripe import StripeClient
from payments.providers.wise import WiseClient, WiseError
from payments.statuses import FUNDED_STATUSES

# The one route this dashboard supports: GBP balance → EUR IBAN (docs/02-dashboard-rnd.md, F7).
SOURCE_CURRENCY = "GBP"
TARGET_CURRENCY = "EUR"

# Stripe receives MYR, a two-decimal currency: RM 10.00 is sent as 1000 sen (docs/rnd/014).
RECEIVE_CURRENCY = "MYR"

INSUFFICIENT_FUNDS_CODES = {"balance.insufficient-funds", "transfer.insufficient_funds"}


class PaymentError(Exception):
    """A step that cannot go ahead, with a message that is safe to show the user."""


@dataclass
class QuoteSummary:
    id: str
    source_amount: Decimal
    source_currency: str
    target_amount: Decimal
    target_currency: str
    rate: Decimal
    fee: Decimal
    expires_at: datetime
    rate_expires_at: datetime | None
    #: Wise's own words when paying from the balance is not possible, e.g. no multi-currency account.
    balance_disabled_reason: str

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


@dataclass
class Recipient:
    id: int
    name: str
    account: str


def parse_quote(data) -> QuoteSummary:
    """Price the quote with the "pay from balance" option, as Wise recommends."""
    options = [option for option in data.get("paymentOptions", []) if option["payIn"] == "BALANCE"]
    if not options:
        raise PaymentError("Wise offers no way to pay this quote from your balance.")
    option = next((option for option in options if option["payOut"] == data.get("payOut")), options[0])
    rate_expires_at = data.get("rateExpirationTime")
    disabled_reason = (option.get("disabledReason") or {}).get("message", "") if option.get("disabled") else ""
    return QuoteSummary(
        id=data["id"],
        source_amount=Decimal(option["sourceAmount"]),
        source_currency=data["sourceCurrency"],
        target_amount=Decimal(option["targetAmount"]),
        target_currency=data["targetCurrency"],
        rate=Decimal(data["rate"]),
        fee=Decimal(option["fee"]["total"]),
        expires_at=parse_datetime(data["expirationTime"]),
        rate_expires_at=parse_datetime(rate_expires_at) if rate_expires_at else None,
        balance_disabled_reason=disabled_reason,
    )


def parse_recipient(data) -> Recipient:
    # The docs show two recipient shapes: `name.fullName` (newer) and `accountHolderName` (older).
    name = data.get("accountHolderName") or data.get("name", {}).get("fullName", "")
    return Recipient(
        id=data["id"],
        name=name,
        account=data.get("longAccountSummary") or f"{data['currency']} account",
    )


# Profile and balances


def list_profiles():
    """Every profile the token can see, cached for an hour to save a call on every page."""
    return cache.get_or_set("wise_profiles", lambda: WiseClient().list_profiles(), 3600)


def get_business_profile():
    """The profile in WISE_PROFILE_ID, else the first BUSINESS one."""
    profiles = list_profiles()
    if settings.WISE_PROFILE_ID:
        matches = [profile for profile in profiles if profile["id"] == settings.WISE_PROFILE_ID]
    else:
        matches = [profile for profile in profiles if profile["type"] == "BUSINESS"]
    if not matches:
        raise PaymentError("No matching Wise profile. Check WISE_PROFILE_ID, or create a business profile.")
    return matches[0]


def get_profile_id():
    return get_business_profile()["id"]


def list_balances():
    return WiseClient().list_balances(get_profile_id())


def create_balance(currency):
    try:
        WiseClient().create_balance(get_profile_id(), currency)
    except WiseError as error:
        if "invalid.profile.type" not in error.codes:
            raise
        raise PaymentError(
            "Wise will not open a balance for this profile yet (invalid.profile.type). Log in to the Wise "
            "website, switch to your business profile and open a multi-currency account, then try again."
        ) from error


def top_up_balance(balance_id, currency, amount):
    if not settings.WISE_IS_SANDBOX:
        raise PaymentError("Top-ups only exist in the Wise sandbox.")
    WiseClient().top_up_balance(get_profile_id(), balance_id, currency, amount)


# Quote and recipient (send-money steps 1 and 2)


def create_quote(source_amount) -> QuoteSummary:
    data = WiseClient().create_quote(get_profile_id(), SOURCE_CURRENCY, TARGET_CURRENCY, source_amount)
    return parse_quote(data)


def get_quote(quote_id) -> QuoteSummary:
    return parse_quote(WiseClient().get_quote(get_profile_id(), quote_id))


def get_account_requirements(quote_id):
    return WiseClient().get_account_requirements(quote_id)


def list_recipients() -> list[Recipient]:
    data = WiseClient().list_recipients(get_profile_id(), TARGET_CURRENCY)
    # The list comes either bare or wrapped in a page object with `content`.
    items = data["content"] if isinstance(data, dict) else data
    return [parse_recipient(item) for item in items]


def create_recipient(account_holder_name, iban) -> Recipient:
    data = WiseClient().create_recipient(get_profile_id(), TARGET_CURRENCY, account_holder_name, iban)
    recipient = parse_recipient(data)
    # The create reply has no masked summary, so build one in Wise's own wording.
    if "longAccountSummary" not in data:
        recipient.account = f"{TARGET_CURRENCY} account ending in {iban[-4:]}"
    return recipient


def update_quote_recipient(quote_id, recipient_id) -> QuoteSummary:
    """Attach the recipient to the quote. The price can change, so show the returned one."""
    return parse_quote(WiseClient().update_quote(get_profile_id(), quote_id, recipient_id))


# Transfer (send-money step 3 and the detail page)


def create_transfer(user, customer_transaction_id, quote_id, recipient: Recipient, reference) -> Transfer:
    """Save the transfer row before any call that could create it at Wise.

    The same `customer_transaction_id` always returns the same row, so a double
    click or a retry can never make a second transfer.
    """
    quote = get_quote(quote_id)
    if quote.is_expired:
        raise PaymentError("This quote has expired. Start again to get a fresh price.")
    transfer, _ = Transfer.objects.get_or_create(
        customer_transaction_id=customer_transaction_id,
        defaults={
            "created_by": user,
            "profile_id": get_profile_id(),
            "quote_id": quote.id,
            "recipient_id": recipient.id,
            "recipient_name": recipient.name,
            "recipient_account": recipient.account,
            "reference": reference,
            "source_amount": quote.source_amount,
            "source_currency": quote.source_currency,
            "target_amount": quote.target_amount,
            "target_currency": quote.target_currency,
            "rate": quote.rate,
            "fee": quote.fee,
        },
    )
    return transfer


def submit_transfer(transfer):
    """Create the transfer at Wise. Safe to call again after a timeout: Wise sees the same ID."""
    if transfer.is_submitted:
        raise PaymentError("This transfer is already at Wise.")
    client = WiseClient(transfer=transfer)
    client.get_transfer_requirements(transfer.quote_id, transfer.recipient_id, transfer.reference)
    data = client.create_transfer(
        transfer.quote_id, transfer.recipient_id, transfer.customer_transaction_id, transfer.reference
    )
    transfer.external_id = data["id"]
    update_transfer_status(transfer, data["status"], StatusChange.Source.CREATE)


def fund_transfer(transfer):
    """Pay the transfer from the balance. Trust the body's `status`, never the HTTP code alone."""
    if not transfer.can_fund:
        raise PaymentError("This transfer cannot be funded in its current state.")
    try:
        data = WiseClient(transfer=transfer).fund_transfer(transfer.profile_id, transfer.external_id)
    except WiseError as error:
        if "payment.exists" not in error.codes:
            transfer.funding_error = ", ".join(error.codes) or f"HTTP {error.status_code}"
            transfer.save()
            raise
        data = {"status": "COMPLETED"}

    if data["status"] != "COMPLETED":
        transfer.funding_error = data.get("errorCode") or data["status"]
        transfer.save()
        if transfer.funding_error in INSUFFICIENT_FUNDS_CODES:
            raise PaymentError(f"Not enough money in your {transfer.source_currency} balance. Top up and try again.")
        raise PaymentError(f"Wise did not fund the transfer ({transfer.funding_error}).")

    transfer.funded_at = timezone.now()
    transfer.funding_error = ""
    transfer.save()
    refresh_transfer(transfer, StatusChange.Source.FUNDING)


def refresh_transfer(transfer, source=StatusChange.Source.REFRESH):
    if not transfer.is_submitted:
        raise PaymentError("This transfer is not at Wise yet. Use Retry first.")
    data = WiseClient(transfer=transfer).get_transfer(transfer.external_id)
    update_transfer_status(transfer, data["status"], source)


def update_transfer_status(transfer, status, source):
    now = timezone.now()
    transfer.last_synced_at = now
    if status in FUNDED_STATUSES and not transfer.is_funded:
        transfer.funded_at = now
    if status != transfer.status:
        transfer.status = status
        transfer.status_changes.create(status=status, source=source)
    transfer.save()


def simulate_next_status(transfer):
    """Sandbox only: ask Wise to move the transfer one step along its lifecycle."""
    step = transfer.next_simulation
    if not settings.WISE_IS_SANDBOX or step is None:
        raise PaymentError("There is no simulation step for this transfer.")
    if transfer.simulated_at and timezone.now() - transfer.simulated_at < timedelta(seconds=5):
        raise PaymentError("Wise needs at least 5 seconds between simulation steps. Try again in a moment.")
    data = WiseClient(transfer=transfer).simulate_transfer_status(transfer.external_id, step)
    transfer.simulated_status = step
    transfer.simulated_at = timezone.now()
    update_transfer_status(transfer, data["status"], StatusChange.Source.SIMULATION)


# Stripe: receive money with a hosted Checkout page


def to_minor_units(amount: Decimal) -> int:
    return int(amount * 100)


def from_minor_units(value: int) -> Decimal:
    return Decimal(value) / 100


def get_stripe_balance():
    """The sandbox balance as rows of (available or pending, amount, currency)."""
    data = StripeClient().get_balance()
    return [
        (kind, from_minor_units(item["amount"]), item["currency"].upper())
        for kind in ("available", "pending")
        for item in data[kind]
    ]


def create_payment(user, amount, description, customer_email) -> Payment:
    """Save the payment, with its idempotency key, before any call to Stripe."""
    return Payment.objects.create(
        created_by=user,
        amount=amount,
        currency=RECEIVE_CURRENCY,
        description=description,
        customer_email=customer_email,
    )


def start_checkout(payment, return_url):
    """Create the Stripe-hosted payment page. Safe to repeat: Stripe sees the same Idempotency-Key."""
    data = StripeClient(payment=payment).create_checkout_session(
        to_minor_units(payment.amount),
        payment.currency,
        payment.description,
        return_url,
        payment.reference_code,
        payment.customer_email,
        payment.idempotency_key,
    )
    payment.external_id = data["id"]
    update_payment_status(payment, data)


def refresh_payment(payment):
    if not payment.is_submitted:
        raise PaymentError("This payment is not at Stripe yet. Use Retry first.")
    update_payment_status(payment, StripeClient(payment=payment).get_checkout_session(payment.external_id))


def update_payment_status(payment, data):
    """Copy a Checkout Session's state onto our row. Paid only when Stripe says `paid`."""
    now = timezone.now()
    payment.status = data["status"] or ""
    payment.payment_status = data["payment_status"]
    payment.payment_intent_id = data.get("payment_intent") or ""
    payment.checkout_url = data.get("url") or ""
    payment.expires_at = datetime.fromtimestamp(data["expires_at"], tz=UTC)
    payment.last_synced_at = now
    if payment.payment_status == "paid" and payment.paid_at is None:
        payment.paid_at = now
    payment.save()
