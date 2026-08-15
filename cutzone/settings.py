"""
Django settings for the CutZone barbershop booking project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# For a school project running locally this default is fine; override
# it with the CUTZONE_SECRET_KEY environment variable in production.
SECRET_KEY = os.environ.get(
    "CUTZONE_SECRET_KEY",
    "django-insecure-cutzone-school-project-key-change-in-production",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("CUTZONE_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]  # local demo / sandbox preview

# Allow form POSTs when the site is accessed through an HTTPS proxy preview
# (harmless for plain local development on http://127.0.0.1:8000).
CSRF_TRUSTED_ORIGINS = ["https://*.e2b.app", "http://localhost:8000", "http://127.0.0.1:8000"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # CutZone apps
    "core",
    "accounts",
    "barbers",
    "services",
    "bookings",
    "reviews",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cutzone.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "cutzone.wsgi.application"

# ---------------------------------------------------------------------------
# Database (SQLite for local development)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation — Owerri, Nigeria
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication redirects
# ---------------------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:post_login_redirect"
LOGOUT_REDIRECT_URL = "core:home"

# ---------------------------------------------------------------------------
# Email — console backend by default so no real provider is required.
# Configure via environment variables for a real SMTP server.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "CUTZONE_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("CUTZONE_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("CUTZONE_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("CUTZONE_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("CUTZONE_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("CUTZONE_EMAIL_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("CUTZONE_FROM_EMAIL", "CutZone <no-reply@cutzone.ng>")

# ---------------------------------------------------------------------------
# Business configuration
# ---------------------------------------------------------------------------
CUTZONE_OPEN_TIME = "08:00"     # shop opens 8:00 AM
CUTZONE_CLOSE_TIME = "19:00"    # shop closes 7:00 PM
CUTZONE_SLOT_STEP_MINUTES = 15  # granularity of bookable time slots
