from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BureauViewSet,
    DirectionViewSet,
    FunctionViewSet,
    GradeViewSet,
    OrganizationLookupViewSet,
    ServiceViewSet,
    SubDirectionViewSet,
)

app_name = "organization"

router = DefaultRouter()
router.register(r"directions", DirectionViewSet, basename="direction")
router.register(r"sub-directions", SubDirectionViewSet, basename="sub-direction")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"bureaux", BureauViewSet, basename="bureau")
router.register(r"functions", FunctionViewSet, basename="function")
router.register(r"grades", GradeViewSet, basename="grade")
router.register(r"lookup", OrganizationLookupViewSet, basename="org-lookup")

urlpatterns = [
    path("", include(router.urls)),
]
