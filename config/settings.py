import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# On by default for local runs; the Docker image sets DJANGO_DEBUG=0.
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
# Refuse to start with the public dev key when DEBUG is off.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "dev-only-insecure-key" if DEBUG else ""
)
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DEBUG is off.")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",
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

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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

# PostgreSQL when Docker Compose provides it, otherwise a local SQLite file.
if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    # Lets gunicorn serve the admin's CSS/JS without a separate web server.
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Console shows warnings and errors by default; DJANGO_LOG_LEVEL=DEBUG adds per-request detail.

CATALOG_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    # Default True would silence Django's own loggers, including request errors.
    "disable_existing_loggers": False,
    "formatters": {
        "console": {"format": "{asctime} {levelname} [{name}] {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "console"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "catalog": {"level": CATALOG_LOG_LEVEL},
        # Admin changes only with DEBUG on; failed logins (warnings) always show.
        "catalog.admin": {"level": CATALOG_LOG_LEVEL if DEBUG else "WARNING"},
        "django": {"level": "INFO"},
        # runserver's request lines; failed requests (4xx/5xx) are always shown.
        "django.server": {
            "level": "INFO" if os.environ.get("DJANGO_ACCESS_LOG") == "1" else "WARNING"
        },
        # SQL is only logged when DEBUG is on.
        "django.db.backends": {
            "level": "DEBUG" if os.environ.get("DJANGO_LOG_SQL") == "1" else "INFO"
        },
    },
}
