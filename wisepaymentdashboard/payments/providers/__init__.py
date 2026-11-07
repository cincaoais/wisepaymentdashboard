"""One module per payment provider. Each is the only code that talks to that provider's API."""

import time

from payments.models import ApiCall


def create_api_call(started, **fields):
    """Record one provider call in the API log. Never pass keys, tokens or bodies."""
    return ApiCall.objects.create(duration_ms=round((time.monotonic() - started) * 1000), **fields)
