from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AnalyticsViewSet,
    DashboardConfigViewSet,
    ExportViewSet,
    KpiViewSet,
    ReportViewSet,
)

app_name = "reporting"

router = DefaultRouter()
router.register(r"analytics", AnalyticsViewSet, basename="analytics")
router.register(r"kpis", KpiViewSet, basename="kpi")
router.register(r"widgets", DashboardConfigViewSet, basename="dashboard-widget")
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"exports", ExportViewSet, basename="data-export")

urlpatterns = [
    path("", include(router.urls)),
]
