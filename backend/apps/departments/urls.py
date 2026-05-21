"""Departments URLs."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import DepartmentViewSet

app_name = "departments"
router = DefaultRouter()
router.register(r"", DepartmentViewSet, basename="department")

urlpatterns = [path("", include(router.urls))]
