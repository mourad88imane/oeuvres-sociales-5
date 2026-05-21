"""Benefits URLs."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import BenefitTypeViewSet, BenefitViewSet

app_name = "benefits"
router = DefaultRouter()
router.register(r"types", BenefitTypeViewSet, basename="benefit-type")
router.register(r"", BenefitViewSet, basename="benefit")
urlpatterns = [path("", include(router.urls))]
