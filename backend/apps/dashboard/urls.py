from django.urls import path

from .views import GlobalDashboardView

app_name = "dashboard"
urlpatterns = [
    path("", GlobalDashboardView.as_view(), name="global-dashboard"),
]
