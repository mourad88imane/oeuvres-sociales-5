"""
============================================================
SETTINGS DÉVELOPPEMENT
============================================================
Activer avec : DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa: F401, F403

# ── Debug activé ──────────────────────────────────────────
DEBUG = True

# ── Hosts permissifs en dev ───────────────────────────────
ALLOWED_HOSTS = ["*"]

# ── Apps supplémentaires en dev ───────────────────────────
INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

# ── Middleware debug toolbar ──────────────────────────────
MIDDLEWARE += [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1", "::1"]

# ── CORS très permissif en dev ────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = False  # Pas besoin de credentials en dev (API same-origin via nginx)

# ── Email via MailHog (Docker) ────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mailhog"
EMAIL_PORT = 1025

# ── Cache simple en dev (mémoire locale) ─────────────────
# Décommenter pour utiliser Redis quand même en dev :
# CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", ...}}

# ── CSP doit matcher Nginx pour éviter le double-header ──
# Note: django-csp v3.8 utilise les settings CSP_* individuels
# (CONTENT_SECURITY_POLICY dict n'est PAS traité par le middleware)
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_STYLE_SRC_ELEM = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_IMG_SRC = ["'self'", "data:", "blob:"]
CSP_FONT_SRC = ["'self'", "data:", "https://fonts.gstatic.com"]
CSP_CONNECT_SRC = ["'self'", "ws://localhost:*", "http://localhost:*"]
CSP_FRAME_SRC = ["'none'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_BASE_URI = ["'self'"]
CSP_FORM_ACTION = ["'self'"]
CSP_REPORT_ONLY = True

# ── JWT plus long en dev pour le confort ─────────────────
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# ── Logging plus verbeux en dev ───────────────────────────
LOGGING["handlers"]["console"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405

# ── Debug toolbar config ──────────────────────────────────
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    "RESULTS_CACHE_SIZE": 100,
    "IS_RUNNING_TESTS": False,
}

# ── Shell Plus (django-extensions) ───────────────────────
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
