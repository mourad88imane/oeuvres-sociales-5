from django.urls import path
from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.MonitoringViewSet.as_view({"get": "dashboard"}), name="monitoring-dashboard"),
    path("api-logs/", views.MonitoringViewSet.as_view({"get": "api_logs"}), name="monitoring-api-logs"),
    path("security-events/", views.MonitoringViewSet.as_view({"get": "security_events"}), name="monitoring-security-events"),
    path("security-events/<uuid:pk>/resolve/", views.MonitoringViewSet.as_view({"post": "resolve"}), name="monitoring-security-resolve"),
    path("endpoint-status/", views.MonitoringViewSet.as_view({"get": "endpoint_status"}), name="monitoring-endpoint-status"),
    path("audit-summary/", views.MonitoringViewSet.as_view({"get": "audit_summary"}), name="monitoring-audit-summary"),
    path("metrics/", views.MonitoringViewSet.as_view({"get": "metrics"}), name="monitoring-metrics"),
]
