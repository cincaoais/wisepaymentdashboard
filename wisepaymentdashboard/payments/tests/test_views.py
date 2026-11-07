import pytest
from django.urls import reverse
from django.utils import timezone

from payments.models import Transfer
from payments.tests.conftest import WISE_URL

pytestmark = pytest.mark.django_db


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


def test_overview_shows_a_friendly_error_when_wise_rejects_the_token(http_mock, logged_in):
    http_mock.get(f"{WISE_URL}/profiles", status=401, json={"error": "invalid_token"})

    page = logged_in.get(reverse("payments:overview")).content.decode()

    assert "Not connected" in page
    assert "Check WISE_API_TOKEN" in page


@pytest.mark.parametrize("amount", ["-5", "1.234", ""])
def test_send_money_rejects_a_bad_amount_without_calling_wise(http_mock, logged_in, amount):
    response = logged_in.post(reverse("payments:send_amount"), {"amount": amount, "reference": "Test"})

    assert response.context["form"].errors["amount"]
    assert len(http_mock.calls) == 0


def test_send_money_wizard_creates_a_transfer_from_the_browser(http_mock, business_profile, quote_data, logged_in):
    quote_url = f"{WISE_URL}/profiles/42/quotes/{quote_data['id']}"
    http_mock.post(f"{WISE_URL}/profiles/42/quotes", json=quote_data)
    http_mock.get(f"{WISE_URL}/accounts", json={"content": []})
    http_mock.post(f"{WISE_URL}/accounts", json={"id": 8692237, "currency": "EUR", "accountHolderName": "Jane Doe"})
    http_mock.patch(quote_url, json=quote_data)
    http_mock.get(quote_url, json=quote_data)
    http_mock.post(f"{WISE_URL}/transfer-requirements", json=[])
    http_mock.post(f"{WISE_URL}/transfers", json={"id": 16521632, "status": "incoming_payment_waiting"})

    logged_in.post(reverse("payments:send_amount"), {"amount": "100", "reference": "Invoice 1"})
    logged_in.post(
        reverse("payments:send_recipient"), {"account_holder_name": "Jane Doe", "iban": "DE89 3704 0044 0532 0130 00"}
    )
    response = logged_in.post(reverse("payments:send_review"))

    transfer = Transfer.objects.get()
    assert response.url == reverse("payments:transfer_detail", args=[transfer.pk])
    assert (transfer.external_id, transfer.status) == (16521632, "incoming_payment_waiting")
    assert (transfer.recipient_name, transfer.recipient_account) == ("Jane Doe", "EUR account ending in 3000")
    assert "send_money" not in logged_in.session


@pytest.mark.parametrize("is_sandbox", [True, False])
def test_sandbox_panel_only_shows_in_the_sandbox(settings, logged_in, transfer, is_sandbox):
    settings.WISE_IS_SANDBOX = is_sandbox
    transfer.funded_at = timezone.now()
    transfer.save()

    page = logged_in.get(reverse("payments:transfer_detail", args=[transfer.pk])).content.decode()

    assert ("Simulate → processing" in page) is is_sandbox
