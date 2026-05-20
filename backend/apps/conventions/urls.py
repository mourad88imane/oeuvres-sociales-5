from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PartnerViewSet,
    ConventionViewSet,
    ConventionDocumentViewSet,
    ConventionAlertViewSet,
)

app_name = "conventions"

router = DefaultRouter()
router.register(r"partners", PartnerViewSet, basename="partner")
router.register(r"conventions", ConventionViewSet, basename="convention")
router.register(r"documents", ConventionDocumentViewSet, basename="convention-document")
router.register(r"alerts", ConventionAlertViewSet, basename="convention-alert")

urlpatterns = [
    path("", include(router.urls)),
]
