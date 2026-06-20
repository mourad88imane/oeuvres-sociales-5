from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.medical_coverage.views import (
    MedicalCoverageTypeViewSet,
    MedicalProviderViewSet,
    MedicalCoverageVoucherViewSet,
    MedicalCoverageRequestViewSet,
)

app_name = "medical_coverage"

router = DefaultRouter()
router.register(r"types", MedicalCoverageTypeViewSet, basename="medical-coverage-type")
router.register(r"providers", MedicalProviderViewSet, basename="medical-provider")
router.register(r"vouchers", MedicalCoverageVoucherViewSet, basename="medical-voucher")
router.register(r"requests", MedicalCoverageRequestViewSet, basename="medical-request")

urlpatterns = [
    path("", include(router.urls)),
]
