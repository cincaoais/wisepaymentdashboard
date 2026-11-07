import uuid

from django.conf import settings
from django.db import models

from payments.statuses import (
    STATUS_GROUPS,
    STATUSES,
    get_checkout_status_info,
    get_next_simulation,
    get_status_info,
)


class Provider(models.TextChoices):
    WISE = "Wise"
    STRIPE = "Stripe"


class TransferQuerySet(models.QuerySet):
    def in_group(self, group):
        if group == "Problem":
            others = [status for status, info in STATUSES.items() if info.group != "Problem"]
            return self.exclude(status__in=others).exclude(status="")
        statuses = [status for status, info in STATUSES.items() if info.group == group]
        if group == "Waiting":
            statuses.append("")
        return self.filter(status__in=statuses)

    def count_by_group(self):
        return {group: self.in_group(group).count() for group in STATUS_GROUPS}


class Transfer(models.Model):
    """One payment this dashboard sent through a provider. Amounts are kept as they were at creation."""

    provider = models.CharField(max_length=20, choices=Provider, default=Provider.WISE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers")
    created_at = models.DateTimeField(auto_now_add=True)

    #: Our idempotency key. Saved before the first call to Wise, reused on every retry.
    customer_transaction_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    #: The provider's own transfer ID. Empty until the provider accepts the transfer.
    external_id = models.BigIntegerField(null=True, blank=True, unique=True)
    profile_id = models.BigIntegerField()
    quote_id = models.CharField(max_length=36)
    recipient_id = models.BigIntegerField()
    recipient_name = models.CharField(max_length=200)
    #: Masked account text from Wise, e.g. "EUR account ending in 3000". Never the full IBAN.
    recipient_account = models.CharField(max_length=200)
    reference = models.CharField(max_length=35)

    source_amount = models.DecimalField(max_digits=19, decimal_places=4)
    source_currency = models.CharField(max_length=3)
    target_amount = models.DecimalField(max_digits=19, decimal_places=4)
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=10)
    fee = models.DecimalField(max_digits=19, decimal_places=4)

    #: The raw status text from Wise, stored even when this app does not know it.
    status = models.CharField(max_length=64, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    funding_error = models.CharField(max_length=100, blank=True)
    #: The last sandbox simulation step that was called, so the next one can be offered.
    simulated_status = models.CharField(max_length=64, blank=True)
    simulated_at = models.DateTimeField(null=True, blank=True)

    objects = TransferQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_code

    @property
    def reference_code(self):
        return f"T-{self.pk:04d}"

    @property
    def is_submitted(self):
        return self.external_id is not None

    @property
    def is_funded(self):
        return self.funded_at is not None

    @property
    def is_final(self):
        if self.status == "cancelled":
            return not self.is_funded
        return self.status_info.is_final

    @property
    def can_fund(self):
        return self.is_submitted and not self.is_funded and self.status == "incoming_payment_waiting"

    @property
    def status_info(self):
        return get_status_info(self.status)

    @property
    def next_simulation(self):
        return get_next_simulation(self.simulated_status) if self.is_funded else None


class StatusChange(models.Model):
    """One row each time a transfer's status was seen to change. The detail page timeline."""

    class Source(models.TextChoices):
        CREATE = "Create"
        FUNDING = "Funding"
        REFRESH = "Refresh"
        SIMULATION = "Simulation"
        COMMAND = "Command"

    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name="status_changes")
    status = models.CharField(max_length=64)
    source = models.CharField(max_length=20, choices=Source)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    @property
    def status_info(self):
        return get_status_info(self.status)


class Payment(models.Model):
    """One payment received through a provider's hosted checkout page (Stripe Checkout)."""

    provider = models.CharField(max_length=20, choices=Provider, default=Provider.STRIPE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    created_at = models.DateTimeField(auto_now_add=True)

    #: Sent as Stripe's `Idempotency-Key`. Saved before the first call, reused on every retry.
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    #: The provider's checkout session ID (`cs_test_…`). Empty until the provider accepts it.
    external_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    payment_intent_id = models.CharField(max_length=255, blank=True)
    checkout_url = models.TextField(blank=True)
    description = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency = models.CharField(max_length=3)

    #: Raw Stripe values: `status` is open/complete/expired, `payment_status` is paid/unpaid/….
    status = models.CharField(max_length=30, blank=True)
    payment_status = models.CharField(max_length=30, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_code

    @property
    def reference_code(self):
        return f"P-{self.pk:04d}"

    @property
    def is_submitted(self):
        return self.external_id is not None

    @property
    def is_open(self):
        return self.status == "open"

    @property
    def status_info(self):
        return get_checkout_status_info(self.status, self.payment_status)


class ApiCall(models.Model):
    """One HTTP call to a provider. No token, no request or response bodies."""

    provider = models.CharField(max_length=20, choices=Provider, default=Provider.WISE)
    created_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    #: Empty when the request never got an answer (timeout, no network).
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField()
    correlation_id = models.CharField(max_length=36)
    trace_id = models.CharField(max_length=100, blank=True)
    error = models.CharField(max_length=255, blank=True)
    transfer = models.ForeignKey(
        Transfer, on_delete=models.SET_NULL, null=True, blank=True, related_name="api_calls"
    )
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="api_calls"
    )

    class Meta:
        ordering = ["-created_at", "-pk"]
