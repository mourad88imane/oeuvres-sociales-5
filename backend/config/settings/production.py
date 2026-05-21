"""
============================================================
SETTINGS PRODUCTION — Durci pour environnement de prod
============================================================
Activer avec : DJANGO_SETTINGS_MODULE=config.settings.production
"""

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403

# ── Mode production ────────────────────────────────────────
DEBUG = False
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # noqa: F405
SITE_URL = config("SITE_URL")

# ── HTTPS obligatoire ─────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ── CORS production ───────────────────────────────────────
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())  # noqa: F405
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",
]

# ── Session ────────────────────────────────────────────────
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ── Database pool ─────────────────────────────────────────
DATABASES["default"]["CONN_MAX_AGE"] = 60  # noqa: F405
DATABASES["default"]["HOST"] = config("DB_HOST", default="pgbouncer")  # noqa: F405
DATABASES["default"]["PORT"] = config("DB_PORT", default="5432")  # noqa: F405
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    "connect_timeout": 10,
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5,
}

# ── Cache ─────────────────────────────────────────────────
CACHES["default"]["LOCATION"] = config("REDIS_URL")  # noqa: F405
CACHES["default"]["TIMEOUT"] = 300  # noqa: F405
CACHES["default"]["KEY_PREFIX"] = "oeuvres:prod"  # noqa: F405

# ── Celery (production tuning) ────────────────────────────
CELERY_BROKER_URL = config("REDIS_URL")
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.2,
    "interval_max": 0.5,
}

# ── Sentry ────────────────────────────────────────────────
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.05,
        profiles_sample_rate=0.05,
        send_default_pii=False,
        environment="production",
        release=config("APP_VERSION", default="1.0.0"),
    )

# ── Email (SMTP production) ───────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# ── DRF Throttling (plus strict en prod) ─────────────────
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "20/hour",
    "user": "500/hour",
    "login": "5/minute",
}

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# ── Logging production (JSON via stdout) ──────────────────
LOGGING["handlers"]["console"] = {  # noqa: F405
    "level": "INFO",
    "class": "logging.StreamHandler",
    "formatter": "json",
    "stream": "ext://sys.stdout",
}
LOGGING["handlers"]["console_json"] = {  # noqa: F405
    "level": "INFO",
    "class": "logging.StreamHandler",
    "formatter": "json",
    "stream": "ext://sys.stdout",
}
LOGGING["loggers"]["django"]["handlers"] = ["console_json"]  # noqa: F405
LOGGING["loggers"]["apps"]["handlers"] = ["console_json"]  # noqa: F405
LOGGING["loggers"]["celery"]["handlers"] = ["console_json"]  # noqa: F405
LOGGING["loggers"]["audit"]["handlers"] = ["console_json"]  # noqa: F405
LOGGING["root"]["handlers"] = ["console"]  # noqa: F405

# ── Axes (brute force) ────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)  # noqa: F405
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = "apps.authentication.utils.axes_lockout_response"

# ── Django REST Framework (pas de browseable API) ─────────
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "rest_framework_simplejwt.authentication.JWTAuthentication",
]

# ── Password validators (renforcé) ────────────────────────
AUTH_PASSWORD_VALIDATORS = [  # noqa: F405
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Security middleware ordering (production) ─────────────
MIDDLEWARE = [  # noqa: F405
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.CsrfExemptApiMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "shared.audit.middleware.AuditMiddleware",
    "apps.monitoring.middleware.APIMonitoringMiddleware",
]

# ── Performances ──────────────────────────────────────────
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 500
SILENCED_SYSTEM_CHECKS = ["security.W004", "security.W008"]
