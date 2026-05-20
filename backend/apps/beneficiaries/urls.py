"""Beneficiaries URLs."""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BeneficiaryViewSet, BeneficiaryGlobalViewSet

app_name = "beneficiaries"

router = DefaultRouter()
router.register(r"", BeneficiaryGlobalViewSet, basename="beneficiary")

urlpatterns = router.urls
