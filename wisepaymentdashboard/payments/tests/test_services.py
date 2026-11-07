import json
from datetime import timedelta
from decimal import Decimal

import pytest
import requests
from django.utils import timezone

from payments import services
from payments.models import StatusChange, Transfer
from payments.providers.wise import WiseError
from payments.services import PaymentError, Recipient
from payments.statuses import get_next_simulation
from payments.tests.conftest import WISE_URL, create_test_transfer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(("profile_id_setting", "expected"), [(None, 42), (1, 1)])
def test_profile_in_use_follows_wise_profile_id(settings, business_profile, profile_id_setting, expected):
    settings.WISE_PROFILE_ID = profile_id_setting

    assert services.get_profile_id() == expected


def test_create_quote_prices_the_pay_from_balance_option(http_mock, business_profile, quote_data):
    http_mock.post(f"{WISE_URL}/profiles/42/quotes", json=quote_data)

    quote = services.create_quote(Decimal("100.10"))

    assert json.loads(http_mock.calls[-1].request.body)["sourceAmount"] == 100.1
    assert (quote.fee, quote.target_amount, quote.rate) == (Decimal("0.52"), Decimal("115.80"), Decimal("1.1641"))


def test_quote_keeps_wise_reason_when_paying_from_balance_is_disabled(http_mock, business_profile, quote_data):
    reason = "Open a multi currency account and add funds to instantly pay for your transfers."
    quote_data["paymentOptions"][1].update(disabled=True, disabledReason={"code": "error.payInmethod.disabled", "message": reason})
    http_mock.post(f"{WISE_URL}/profiles/42/quotes", json=quote_data)

    assert services.create_quote(Decimal("100")).balance_disabled_reason == reason


def test_create_balance_explains_a_profile_without_a_multi_currency_account(http_mock, business_profile):
    http_mock.post(f"{WISE_URL}/profiles/42/balances", status=403, json={"errors": [{"code": "invalid.profile.type"}]})

    with pytest.raises(PaymentError, match="open a multi-currency account"):
        services.create_balance("GBP")


def test_retry_after_a_timeout_reuses_the_same_customer_transaction_id(http_mock, business_profile, quote_data, user):
    http_mock.get(f"{WISE_URL}/profiles/42/quotes/{quote_data['id']}", json=quote_data)
    http_mock.post(f"{WISE_URL}/transfer-requirements", json=[])
    http_mock.post(f"{WISE_URL}/transfers", body=requests.Timeout())
    recipient = Recipient(id=8692237, name="Jane Doe", account="EUR account ending in 3000")
    customer_transaction_id = "54a6bc09-cef9-49a8-9041-f1f0c654cd88"

    transfer = services.create_transfer(user, customer_transaction_id, quote_data["id"], recipient, "Invoice 1")
    with pytest.raises(WiseError):
        services.submit_transfer(transfer)
    assert Transfer.objects.get().external_id is None

    http_mock.replace("POST", f"{WISE_URL}/transfers", json={"id": 16521632, "status": "incoming_payment_waiting"})
    services.submit_transfer(transfer)

    transfer_calls = [call for call in http_mock.calls if call.request.url.endswith("/transfers")]
    sent_ids = [json.loads(call.request.body)["customerTransactionId"] for call in transfer_calls]
    assert sent_ids == [customer_transaction_id, customer_transaction_id]
    assert Transfer.objects.get().external_id == 16521632
    assert transfer.status_changes.get().source == StatusChange.Source.CREATE


@pytest.mark.parametrize(
    ("funding", "is_funded", "error"),
    [
        ({"type": "BALANCE", "status": "COMPLETED", "balanceTransactionId": 1}, True, None),
        ({"type": "BALANCE", "status": "REJECTED", "errorCode": "balance.insufficient-funds"}, False, "Not enough money"),
    ],
)
def test_fund_transfer_trusts_the_status_in_the_body(http_mock, transfer, funding, is_funded, error):
    http_mock.post(f"{WISE_URL}/profiles/42/transfers/100/payments", status=201, json=funding)
    http_mock.get(f"{WISE_URL}/transfers/100", json={"id": 100, "status": "processing"})

    if error:
        with pytest.raises(PaymentError, match=error):
            services.fund_transfer(transfer)
    else:
        services.fund_transfer(transfer)

    transfer.refresh_from_db()
    assert transfer.is_funded is is_funded
    assert transfer.funding_error == funding.get("errorCode", "")


@pytest.mark.parametrize(
    ("last_simulated", "expected"),
    [("", "processing"), ("processing", "funds_converted"), ("outgoing_payment_sent", "bounced_back"), ("funds_refunded", None)],
)
def test_next_simulation_follows_the_order_wise_accepts(last_simulated, expected):
    assert get_next_simulation(last_simulated) == expected


def test_simulation_waits_5_seconds_between_steps_without_calling_wise(http_mock, transfer):
    transfer.funded_at = timezone.now()
    transfer.simulated_status = "processing"
    transfer.simulated_at = timezone.now() - timedelta(seconds=2)

    with pytest.raises(PaymentError, match="5 seconds"):
        services.simulate_next_status(transfer)

    assert len(http_mock.calls) == 0


def test_refresh_records_a_status_change_only_when_the_status_changes(http_mock, transfer):
    http_mock.get(f"{WISE_URL}/transfers/100", json={"id": 100, "status": "processing"})

    services.refresh_transfer(transfer)
    services.refresh_transfer(transfer)

    assert list(transfer.status_changes.values_list("status", flat=True)) == ["processing"]
    assert transfer.is_funded


def test_status_groups_put_unrecognised_statuses_under_problem(user):
    for status in ["", "processing", "bounced_back", "something_new"]:
        create_test_transfer(user, status=status)

    waiting = set(Transfer.objects.in_group("Waiting").values_list("status", flat=True))
    problem = set(Transfer.objects.in_group("Problem").values_list("status", flat=True))

    assert (waiting, problem) == ({""}, {"bounced_back", "something_new"})
