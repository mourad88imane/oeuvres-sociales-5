"""Finance URLs."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    BudgetViewSet,
    FinanceDashboardView,
    FinancialAlertViewSet,
    FinancialEntryViewSet,
    FiscalYearViewSet,
    PaymentBatchViewSet,
    PaymentViewSet,
)

app_name = "finance"
router = DefaultRouter()
router.register(r"fiscal-years", FiscalYearViewSet, basename="fiscal-year")
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"payment-batches", PaymentBatchViewSet, basename="payment-batch")
router.register(r"entries", FinancialEntryViewSet, basename="entry")
router.register(r"alerts", FinancialAlertViewSet, basename="alert")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", FinanceDashboardView.as_view(), name="dashboard"),
]
