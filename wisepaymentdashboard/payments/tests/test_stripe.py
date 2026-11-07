from decimal import Decimal
from urllib.parse import parse_qs

import pytest
import requests
from django.urls import reverse

from payments import services
from payments.models import ApiCall, Payment
from payments.providers.stripe import StripeClient, StripeError
from payments.tests.conftest import STRIPE_KEY, STRIPE_URL

pytestmark = pytest.mark.django_db


def test_checkout_request_is_form_encoded_with_key_version_and_idempotency_key(http_mock, checkout_session):
    http_mock.post(f"{STRIPE_URL}/checkout/sessions", json=checkout_session, headers={"Request-Id": "req_1"})

    StripeClient().create_checkout_session(1000, "MYR", "Test order", "http://testserver/back/", "P-0001", "", "key-1")

    request = http_mock.calls[0].request
    body = parse_qs(request.body)
    assert body["line_items[0][price_data][unit_amount]"] == ["1000"]
    assert body["line_items[0][price_data][currency]"] == ["myr"]
    assert request.headers["Authorization"] == f"Bearer {STRIPE_KEY}"
    assert (request.headers["Idempotency-Key"], request.headers["Stripe-Version"]) == ("key-1", "2026-09-30.endive")
    call = ApiCall.objects.get()
    assert (call.provider, call.path, call.trace_id) == ("Stripe", "/v1/checkout/sessions", "req_1")
    assert STRIPE_KEY not in str(vars(call))


@pytest.mark.parametrize(
    ("status", "error", "message_part"),
    [
        (401, {"type": "invalid_request_error", "message": "Invalid API Key provided"}, "STRIPE_SECRET_KEY"),
        (400, {"type": "invalid_request_error", "code": "url_invalid", "message": "Not a valid URL"}, "Not a valid URL"),
    ],
)
def test_error_responses_become_a_stripe_error_with_a_friendly_message(http_mock, status, error, message_part):
    http_mock.get(f"{STRIPE_URL}/balance", status=status, json={"error": error})

    with pytest.raises(StripeError, match=message_part):
        StripeClient().get_balance()

    assert ApiCall.objects.get().error == error.get("code", error["type"])


def test_live_keys_are_refused_before_any_call(settings, http_mock):
    settings.STRIPE_SECRET_KEY = "sk_live_real-money"

    with pytest.raises(StripeError, match="sandbox key"):
        StripeClient().get_balance()

    assert len(http_mock.calls) == 0


def test_retry_after_a_timeout_reuses_the_same_idempotency_key(http_mock, checkout_session, user):
    http_mock.post(f"{STRIPE_URL}/checkout/sessions", body=requests.Timeout())
    payment = services.create_payment(user, Decimal("10.00"), "Test order", "")

    with pytest.raises(StripeError):
        services.start_checkout(payment, "http://testserver/back/")
    assert Payment.objects.get().external_id is None

    http_mock.replace("POST", f"{STRIPE_URL}/checkout/sessions", json=checkout_session)
    services.start_checkout(payment, "http://testserver/back/")

    keys = [call.request.headers["Idempotency-Key"] for call in http_mock.calls]
    assert keys == [str(payment.idempotency_key)] * 2
    assert (payment.external_id, payment.checkout_url) == ("cs_test_123", checkout_session["url"])


@pytest.mark.parametrize(
    ("payment_status", "is_paid", "label"),
    [("paid", True, "Paid"), ("unpaid", False, "Processing")],
)
def test_refresh_marks_a_payment_paid_only_when_stripe_says_paid(
    http_mock, checkout_session, user, payment_status, is_paid, label
):
    payment = services.create_payment(user, Decimal("10.00"), "Test order", "")
    payment.external_id = "cs_test_123"
    checkout_session.update(status="complete", payment_status=payment_status, url=None)
    http_mock.get(f"{STRIPE_URL}/checkout/sessions/cs_test_123", json=checkout_session)

    services.refresh_payment(payment)

    payment.refresh_from_db()
    assert (bool(payment.paid_at), payment.payment_status, payment.status_info.label) == (is_paid, payment_status, label)


def test_receive_money_sends_the_browser_to_stripe_and_back(http_mock, checkout_session, client, user):
    client.force_login(user)
    http_mock.post(f"{STRIPE_URL}/checkout/sessions", json=checkout_session)

    response = client.post(reverse("payments:receive_money"), {"amount": "10.00", "description": "Test order"})

    payment = Payment.objects.get()
    assert response.url == checkout_session["url"]
    assert parse_qs(http_mock.calls[0].request.body)["success_url"] == [
        f"http://testserver{reverse('payments:payment_return', args=[payment.pk])}"
    ]

    checkout_session.update(status="complete", payment_status="paid", payment_intent="pi_123", url=None)
    http_mock.get(f"{STRIPE_URL}/checkout/sessions/cs_test_123", json=checkout_session)
    page = client.get(reverse("payments:payment_return", args=[payment.pk]), follow=True).content.decode()

    assert "Payment received." in page
    assert Payment.objects.get().payment_intent_id == "pi_123"
