from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import LoanViewSet

app_name = "loans"
router = DefaultRouter()
router.register(r"", LoanViewSet, basename="loan")
urlpatterns = [path("", include(router.urls))]
