"""The only module that talks to the Wise API.

Every call goes through `WiseClient.request`, which adds the token, parses
numbers as `Decimal`, writes one `ApiCall` row and turns failures into `WiseError`.
"""

import json
import logging
import time
import uuid
from decimal import Decimal

import requests
from django.conf import settings

from payments.models import Provider
from payments.providers import create_api_call

logger = logging.getLogger(__name__)

FRIENDLY_MESSAGES = {
    401: "Wise rejected the API token. Check WISE_API_TOKEN in your .env file.",
    403: "Wise refused this action for your token or profile.",
    404: "Wise could not find this item. Check the ID and that you are using the right environment.",
    409: "This clashes with the item's current state at Wise. Refresh and try again.",
    429: "Too many requests to Wise. Wait a moment and try again.",
}


class WiseError(Exception):
    def __init__(self, status_code, errors=(), trace_id="", is_sca_required=False):
        self.status_code = status_code
        self.errors = list(errors)
        self.trace_id = trace_id
        self.is_sca_required = is_sca_required
        super().__init__(self.message)

    @property
    def codes(self):
        return [error["code"] for error in self.errors]

    @property
    def message(self):
        if self.status_code is None:
            return "Could not reach Wise. Check your internet connection and try again."
        if self.is_sca_required:
            return "Wise needs extra approval (SCA) for this. Do it in the Wise website instead."
        if self.status_code in FRIENDLY_MESSAGES:
            codes = ", ".join(self.codes)
            return f"{FRIENDLY_MESSAGES[self.status_code]} ({codes})" if codes else FRIENDLY_MESSAGES[self.status_code]
        if self.status_code >= 500:
            return f"Wise is having problems right now (HTTP {self.status_code}). Try again later."
        details = "; ".join(
            f"{error['path']}: {error['message']}" if error["path"] else error["message"] or error["code"]
            for error in self.errors
        )
        return f"Wise rejected the request: {details or f'HTTP {self.status_code}'}"


def parse_errors(data):
    """Read the error shapes Wise uses: an `errors` list, an OAuth `error`, a single object, or a problem."""
    if not isinstance(data, dict):
        return []
    items = data.get("errors") or [data]
    return [
        {
            "code": str(item.get("code") or item.get("error") or item.get("title") or ""),
            "path": str(item.get("path") or ""),
            "message": str(item.get("message") or item.get("detail") or ""),
        }
        for item in items
    ]


class WiseClient:
    def __init__(self, transfer=None):
        #: Every call made by this client is linked to this transfer in the API log.
        self.transfer = transfer
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {settings.WISE_API_TOKEN}"

    def request(self, method, path, *, body=None, params=None, headers=None):
        path = f"/{settings.WISE_API_VERSION}{path}"
        correlation_id = str(uuid.uuid4())
        request_headers = {"X-External-Correlation-Id": correlation_id, "Content-Type": "application/json"}
        request_headers.update(headers or {})
        started = time.monotonic()
        try:
            response = self.session.request(
                method,
                settings.WISE_BASE_URL + path,
                # json has no Decimal type; float text is exact for amounts under 15 digits.
                data=None if body is None else json.dumps(body, default=float),
                params=params,
                headers=request_headers,
                timeout=20,
            )
        except requests.RequestException as exc:
            self._log(method, path, None, started, correlation_id, error=type(exc).__name__)
            raise WiseError(None) from exc

        try:
            data = response.json(parse_float=Decimal) if response.content else None
        except ValueError:
            data = None
        trace_id = response.headers.get("x-trace-id", "")

        if response.status_code >= 400:
            error = WiseError(
                response.status_code,
                parse_errors(data),
                trace_id,
                is_sca_required=response.status_code == 403 and "x-2fa-approval" in response.headers,
            )
            short_error = ", ".join(error.codes) or response.reason
            self._log(method, path, response.status_code, started, correlation_id, trace_id, short_error)
            logger.warning("Wise %s %s failed: %s %s", method, path, response.status_code, short_error)
            raise error

        self._log(method, path, response.status_code, started, correlation_id, trace_id)
        return data

    def _log(self, method, path, status_code, started, correlation_id, trace_id="", error=""):
        create_api_call(
            started,
            provider=Provider.WISE,
            method=method,
            path=path,
            status_code=status_code,
            correlation_id=correlation_id,
            trace_id=trace_id,
            error=error[:255],
            transfer=self.transfer,
        )

    # Profiles and balances

    def list_profiles(self):
        return self.request("GET", "/profiles")

    def list_balances(self, profile_id):
        return self.request("GET", f"/profiles/{profile_id}/balances", params={"types": "STANDARD"})

    def create_balance(self, profile_id, currency):
        return self.request(
            "POST",
            f"/profiles/{profile_id}/balances",
            body={"currency": currency, "type": "STANDARD"},
            headers={"X-idempotence-uuid": str(uuid.uuid4())},
        )

    # Quotes and recipients

    def create_quote(self, profile_id, source_currency, target_currency, source_amount):
        body = {
            "sourceCurrency": source_currency,
            "targetCurrency": target_currency,
            "sourceAmount": source_amount,
            "targetAccount": None,
        }
        return self.request("POST", f"/profiles/{profile_id}/quotes", body=body)

    def get_quote(self, profile_id, quote_id):
        return self.request("GET", f"/profiles/{profile_id}/quotes/{quote_id}")

    def update_quote(self, profile_id, quote_id, recipient_id):
        return self.request(
            "PATCH",
            f"/profiles/{profile_id}/quotes/{quote_id}",
            body={"targetAccount": recipient_id},
            headers={"Content-Type": "application/merge-patch+json"},
        )

    def get_account_requirements(self, quote_id):
        return self.request(
            "GET", f"/quotes/{quote_id}/account-requirements", headers={"Accept-Minor-Version": "1"}
        )

    def list_recipients(self, profile_id, currency):
        return self.request("GET", "/accounts", params={"profileId": profile_id, "currency": currency})

    def create_recipient(self, profile_id, currency, account_holder_name, iban):
        body = {
            "profile": profile_id,
            "currency": currency,
            "type": "iban",
            "accountHolderName": account_holder_name,
            "ownedByCustomer": False,
            "details": {"legalType": "PRIVATE", "iban": iban},
        }
        return self.request("POST", "/accounts", body=body)

    # Transfers

    def get_transfer_requirements(self, quote_id, recipient_id, reference):
        body = {"targetAccount": recipient_id, "quoteUuid": quote_id, "details": {"reference": reference}}
        return self.request("POST", "/transfer-requirements", body=body)

    def create_transfer(self, quote_id, recipient_id, customer_transaction_id, reference):
        body = {
            "targetAccount": recipient_id,
            "quoteUuid": quote_id,
            "customerTransactionId": str(customer_transaction_id),
            "details": {"reference": reference},
        }
        return self.request("POST", "/transfers", body=body)

    def get_transfer(self, transfer_id):
        return self.request("GET", f"/transfers/{transfer_id}")

    def fund_transfer(self, profile_id, transfer_id):
        return self.request(
            "POST", f"/profiles/{profile_id}/transfers/{transfer_id}/payments", body={"type": "BALANCE"}
        )

    # Sandbox simulations

    def simulate_transfer_status(self, transfer_id, status):
        return self.request("GET", f"/simulation/transfers/{transfer_id}/{status}")

    def top_up_balance(self, profile_id, balance_id, currency, amount):
        body = {"profileId": profile_id, "balanceId": balance_id, "currency": currency, "amount": amount}
        return self.request("POST", "/simulation/balance/topup", body=body)
