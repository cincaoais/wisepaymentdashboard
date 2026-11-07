"""The only module that talks to the Stripe API.

Every call goes through `StripeClient.request`, which adds the secret key and the
pinned API version, writes one `ApiCall` row and turns failures into `StripeError`.
"""

import logging
import time
import uuid

import requests
from django.conf import settings

from payments.models import Provider
from payments.providers import create_api_call

logger = logging.getLogger(__name__)

FRIENDLY_MESSAGES = {
    401: "Stripe rejected the secret key. Check STRIPE_SECRET_KEY in your .env file.",
    403: "Stripe does not allow this action for your key.",
    429: "Too many requests to Stripe. Wait a moment and try again.",
}


class StripeError(Exception):
    def __init__(self, status_code, code="", detail="", request_id=""):
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.request_id = request_id
        super().__init__(self.message)

    @property
    def message(self):
        if self.status_code is None:
            return self.detail or "Could not reach Stripe. Check your internet connection and try again."
        if self.status_code in FRIENDLY_MESSAGES:
            return FRIENDLY_MESSAGES[self.status_code]
        if self.status_code >= 500:
            return f"Stripe is having problems right now (HTTP {self.status_code}). Try again later."
        return f"Stripe rejected the request: {self.detail or self.code or f'HTTP {self.status_code}'}"


class StripeClient:
    def __init__(self, payment=None):
        if not settings.STRIPE_SECRET_KEY.startswith(("sk_test_", "rk_test_")):
            raise StripeError(None, detail="Set STRIPE_SECRET_KEY in .env to a sandbox key (sk_test_… or rk_test_…).")
        #: Every call made by this client is linked to this payment in the API log.
        self.payment = payment

    def request(self, method, path, *, data=None, idempotency_key=None):
        path = f"/v1{path}"
        correlation_id = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
            "Stripe-Version": settings.STRIPE_API_VERSION,
        }
        if idempotency_key:
            headers["Idempotency-Key"] = str(idempotency_key)
        started = time.monotonic()
        try:
            response = requests.request(
                method, "https://api.stripe.com" + path, data=data, headers=headers, timeout=20
            )
        except requests.RequestException as exc:
            self._log(method, path, None, started, correlation_id, error=type(exc).__name__)
            raise StripeError(None) from exc

        try:
            body = response.json()
        except ValueError:
            body = {}
        request_id = response.headers.get("Request-Id", "")

        if response.status_code >= 400:
            details = body.get("error") or {}
            error = StripeError(
                response.status_code, details.get("code") or "", details.get("message") or "", request_id
            )
            short_error = details.get("code") or details.get("type") or response.reason
            self._log(method, path, response.status_code, started, correlation_id, request_id, short_error)
            logger.warning("Stripe %s %s failed: %s %s", method, path, response.status_code, short_error)
            raise error

        self._log(method, path, response.status_code, started, correlation_id, request_id)
        return body

    def _log(self, method, path, status_code, started, correlation_id, request_id="", error=""):
        create_api_call(
            started,
            provider=Provider.STRIPE,
            method=method,
            path=path,
            status_code=status_code,
            correlation_id=correlation_id,
            trace_id=request_id,
            error=error[:255],
            payment=self.payment,
        )

    def get_balance(self):
        return self.request("GET", "/balance")

    def create_checkout_session(
        self, amount_minor, currency, description, return_url, reference, customer_email, idempotency_key
    ):
        # Stripe takes form-encoded bodies; nested fields are written as `a[0][b]` keys.
        data = {
            "mode": "payment",
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][unit_amount]": amount_minor,
            "line_items[0][price_data][product_data][name]": description,
            "success_url": return_url,
            "cancel_url": return_url,
            "client_reference_id": reference,
        }
        if customer_email:
            data["customer_email"] = customer_email
        return self.request("POST", "/checkout/sessions", data=data, idempotency_key=idempotency_key)

    def get_checkout_session(self, session_id):
        return self.request("GET", f"/checkout/sessions/{session_id}")
