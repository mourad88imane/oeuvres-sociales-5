"""
============================================================
URLs PRINCIPALES — config/urls.py
============================================================
"""

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# ── URL Patterns ──────────────────────────────────────────
urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),
    # API v1 — toutes les routes préfixées par /api/v1/
    path(
        "api/v1/",
        include(
            [
                # Authentification (login, logout, refresh, me)
                path("auth/", include("apps.authentication.urls", namespace="auth")),
                # Modules métier
                path("users/", include("apps.users.urls", namespace="users")),
                path("departments/", include("apps.departments.urls", namespace="departments")),
                path("employees/", include("apps.employees.urls", namespace="employees")),
                path(
                    "beneficiaries/", include("apps.beneficiaries.urls", namespace="beneficiaries")
                ),
                path("benefits/", include("apps.benefits.urls", namespace="benefits")),
                path("finance/", include("apps.finance.urls", namespace="finance")),
                path("conventions/", include("apps.conventions.urls", namespace="conventions")),
                path("reporting/", include("apps.reporting.urls", namespace="reporting")),
                path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
                path(
                    "notifications/",
                    include("shared.notifications.urls", namespace="notifications"),
                ),
                path("monitoring/", include("apps.monitoring.urls", namespace="monitoring")),
                path("audit/", include("shared.audit.urls", namespace="audit")),
                path("ai/", include("shared.ai.urls", namespace="ai")),
            ]
        ),
    ),
    # Documentation API (OpenAPI 3 / Swagger)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# ── Dev uniquement : debug toolbar + media files ──────────
if settings.DEBUG:
    import debug_toolbar

    from django.conf.urls.static import static

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
