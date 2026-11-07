from django.conf import settings


def providers(request):
    return {
        "wise_is_sandbox": settings.WISE_IS_SANDBOX,
        "wise_api_url": f"{settings.WISE_BASE_URL}/{settings.WISE_API_VERSION}",
        "wise_website_url": "https://wise-sandbox.com" if settings.WISE_IS_SANDBOX else "https://wise.com",
        "stripe_is_sandbox": settings.STRIPE_SECRET_KEY.startswith(("sk_test_", "rk_test_")),
    }
