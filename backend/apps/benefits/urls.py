"""Benefits URLs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BenefitViewSet, BenefitTypeViewSet

app_name = "benefits"
router   = DefaultRouter()
router.register(r"types",   BenefitTypeViewSet, basename="benefit-type")
router.register(r"",        BenefitViewSet,     basename="benefit")
urlpatterns = [path("", include(router.urls))]
