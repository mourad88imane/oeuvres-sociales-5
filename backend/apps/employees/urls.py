"""Employee URLs with nested beneficiaries."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

try:
    from rest_framework_nested import routers as nested_routers

    HAS_NESTED = True
except ImportError:
    HAS_NESTED = False

from apps.beneficiaries.views import BeneficiaryViewSet

from .views import EmployeeViewSet

app_name = "employees"
router = DefaultRouter()
router.register(r"", EmployeeViewSet, basename="employee")

if HAS_NESTED:
    bene_router = nested_routers.NestedDefaultRouter(router, r"", lookup="employee")
    bene_router.register(r"beneficiaries", BeneficiaryViewSet, basename="employee-beneficiary")
    urlpatterns = [path("", include(router.urls)), path("", include(bene_router.urls))]
else:
    urlpatterns = [
        path("", include(router.urls)),
        path(
            "<uuid:employee_pk>/beneficiaries/",
            BeneficiaryViewSet.as_view({"get": "list", "post": "create"}),
            name="beneficiary-list",
        ),
        path(
            "<uuid:employee_pk>/beneficiaries/<uuid:pk>/",
            BeneficiaryViewSet.as_view(
                {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
            ),
            name="beneficiary-detail",
        ),
    ]
