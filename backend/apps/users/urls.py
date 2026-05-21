"""Users URL configuration."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import UserViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
