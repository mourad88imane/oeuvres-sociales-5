from django.urls import path
from . import views

app_name = "audit"

urlpatterns = [
    path("logs/", views.AuditViewSet.as_view({"get": "logs"}), name="audit-logs"),
    path("stats/", views.AuditViewSet.as_view({"get": "stats"}), name="audit-stats"),
    path("validations/", views.AuditViewSet.as_view({"get": "validations"}), name="audit-validations"),
    path("validation-stats/", views.AuditViewSet.as_view({"get": "validation_stats"}), name="audit-validation-stats"),
]
