"""Shared test setup. Tests never call the real Wise API: `responses` fakes every HTTP call.

The sample bodies follow the examples in Wise's docs (see docs/rnd/). Swap in
real sandbox responses once you have them.
"""

import pytest
import responses
from django.core.cache import cache

from payments.models import Transfer

WISE_URL = "https://api.wise-sandbox.com/2026Q4"
TOKEN = "test-token-must-never-be-logged"
STRIPE_URL = "https://api.stripe.com/v1"
STRIPE_KEY = "sk_test_key-must-never-be-logged"


@pytest.fixture(autouse=True)
def wise_settings(settings):
    settings.WISE_API_TOKEN = TOKEN
    settings.WISE_BASE_URL = "https://api.wise-sandbox.com"
    settings.WISE_API_VERSION = "2026Q4"
    settings.WISE_IS_SANDBOX = True
    settings.WISE_PROFILE_ID = None
    settings.STRIPE_SECRET_KEY = STRIPE_KEY
    settings.STRIPE_API_VERSION = "2026-09-30.endive"
    cache.clear()


@pytest.fixture
def http_mock():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


@pytest.fixture
def business_profile(http_mock):
    profiles = [{"id": 1, "type": "PERSONAL"}, {"id": 42, "type": "BUSINESS", "businessName": "Test Ltd"}]
    http_mock.get(f"{WISE_URL}/profiles", json=profiles)


@pytest.fixture
def quote_data():
    return {
        "id": "11144c35-9fe8-4c32-b7fd-d05c2a7734bf",
        "sourceCurrency": "GBP",
        "targetCurrency": "EUR",
        "rate": 1.1641,
        "payOut": "BANK_TRANSFER",
        "expirationTime": "2099-01-01T12:30:00Z",
        "rateExpirationTime": "2099-01-03T12:00:00Z",
        "paymentOptions": [
            {"payIn": "BANK_TRANSFER", "payOut": "BANK_TRANSFER", "sourceAmount": 100, "targetAmount": 115.95,
             "fee": {"total": 0.39}},
            {"payIn": "BALANCE", "payOut": "BANK_TRANSFER", "sourceAmount": 100, "targetAmount": 115.80,
             "fee": {"total": 0.52}},
        ],
    }


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user("intern", password="test-password")


@pytest.fixture
def transfer(user):
    return create_test_transfer(user, external_id=100, status="incoming_payment_waiting")


def create_test_transfer(user, **fields):
    return Transfer.objects.create(
        created_by=user,
        profile_id=42,
        quote_id="11144c35-9fe8-4c32-b7fd-d05c2a7734bf",
        recipient_id=8692237,
        recipient_name="Jane Doe",
        recipient_account="EUR account ending in 3000",
        reference="Test payment",
        source_amount="100",
        source_currency="GBP",
        target_amount="115.80",
        target_currency="EUR",
        rate="1.1641",
        fee="0.52",
        **fields,
    )


@pytest.fixture
def checkout_session():
    return {
        "id": "cs_test_123",
        "object": "checkout.session",
        "status": "open",
        "payment_status": "unpaid",
        "url": "https://checkout.stripe.com/c/pay/cs_test_123",
        "expires_at": 4102444800,
        "payment_intent": None,
        "amount_total": 1000,
        "currency": "myr",
    }
