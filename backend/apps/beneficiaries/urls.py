"""Beneficiaries URLs."""

from rest_framework.routers import DefaultRouter

from .views import BeneficiaryGlobalViewSet

app_name = "beneficiaries"

router = DefaultRouter()
router.register(r"", BeneficiaryGlobalViewSet, basename="beneficiary")

urlpatterns = router.urls
