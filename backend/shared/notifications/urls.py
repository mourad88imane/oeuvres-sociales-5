"""Notification URLs."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import NotificationPreferenceViewSet, NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

pref_router = DefaultRouter()
pref_router.register(r"preferences", NotificationPreferenceViewSet, basename="preference")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(pref_router.urls)),
]
