from decimal import Decimal

import pytest
import requests

from payments.models import ApiCall
from payments.providers.wise import WiseClient, WiseError
from payments.tests.conftest import TOKEN, WISE_URL

pytestmark = pytest.mark.django_db


def test_request_parses_numbers_as_decimal_and_logs_the_call_without_the_token(http_mock):
    http_mock.get(f"{WISE_URL}/profiles", json=[{"id": 42, "rate": 1.1641}], headers={"x-trace-id": "trace-1"})

    profiles = WiseClient().list_profiles()

    assert profiles[0]["rate"] == Decimal("1.1641")
    assert http_mock.calls[0].request.headers["Authorization"] == f"Bearer {TOKEN}"
    call = ApiCall.objects.get()
    assert (call.method, call.path, call.status_code, call.trace_id) == ("GET", "/2026Q4/profiles", 200, "trace-1")
    assert TOKEN not in str(vars(call))


@pytest.mark.parametrize(
    ("status", "body", "headers", "codes", "message_part"),
    [
        (
            422,
            {"errors": [{"code": "NOT_VALID", "message": "Please specify an IBAN.", "path": "IBAN"}]},
            {},
            ["NOT_VALID"],
            "IBAN: Please specify an IBAN.",
        ),
        (401, {"error": "invalid_token", "error_description": "Invalid token"}, {}, ["invalid_token"], "WISE_API_TOKEN"),
        (403, {"errors": [{"code": "sca.required"}]}, {"x-2fa-approval": "abc"}, ["sca.required"], "SCA"),
        (403, {"errors": [{"code": "invalid.profile.type"}]}, {}, ["invalid.profile.type"], "(invalid.profile.type)"),
    ],
)
def test_error_responses_become_a_wise_error_with_a_friendly_message(http_mock, status, body, headers, codes, message_part):
    http_mock.post(f"{WISE_URL}/accounts", status=status, json=body, headers=headers)

    with pytest.raises(WiseError) as raised:
        WiseClient().create_recipient(42, "EUR", "Jane Doe", "DE00")

    assert raised.value.codes == codes
    assert message_part in str(raised.value)
    assert ApiCall.objects.get().error == ", ".join(codes)


def test_network_failure_raises_a_wise_error_and_logs_a_call_with_no_answer(http_mock):
    http_mock.get(f"{WISE_URL}/transfers/100", body=requests.ConnectionError("down"))

    with pytest.raises(WiseError, match="Could not reach Wise"):
        WiseClient().get_transfer(100)

    call = ApiCall.objects.get()
    assert (call.status_code, call.error) == (None, "ConnectionError")
