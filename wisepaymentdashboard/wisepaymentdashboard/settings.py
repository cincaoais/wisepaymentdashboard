"""
Django settings for wisepaymentdashboard project.

Every secret or machine-specific value comes from the `.env` file in the
workspace root (see `.env.example`).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wisepaymentdashboard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "payments.context_processors.providers",
            ],
        },
    },
]

WSGI_APPLICATION = "wisepaymentdashboard.wsgi.application"


# Database: SQLite by default. Set DATABASE_URL in .env to use PostgreSQL.

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication

AUTH_USER_MODEL = "users.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "payments:overview"
LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en-gb"
TIME_ZONE = env("DJANGO_TIME_ZONE", default="Asia/Kuala_Lumpur")
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"


# Email

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# Wise

WISE_API_TOKEN = env("WISE_API_TOKEN", default="")
WISE_BASE_URL = env("WISE_BASE_URL", default="https://api.wise-sandbox.com")
WISE_API_VERSION = env("WISE_API_VERSION", default="2026Q4")
WISE_PROFILE_ID = env.int("WISE_PROFILE_ID", default=None)
WISE_IS_SANDBOX = "sandbox" in WISE_BASE_URL


# Stripe (sandbox keys only: sk_test_… or rk_test_…)

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_API_VERSION = env("STRIPE_API_VERSION", default="2026-09-30.endive")


# Logging: Wise client errors go to the console. The token is never logged.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"payments": {"handlers": ["console"], "level": "INFO"}},
}
