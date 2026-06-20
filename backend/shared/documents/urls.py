from django.urls import path

from . import views

app_name = "shared_documents"

urlpatterns = [
    path("", views.DocumentViewSet.as_view({"get": "list", "post": "create"}), name="document-list"),
    path("upload/", views.DocumentViewSet.as_view({"post": "upload"}), name="document-upload"),
    path("categories/", views.DocumentViewSet.as_view({"get": "categories"}), name="document-categories"),
    path("<uuid:pk>/", views.DocumentViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="document-detail"),
    path("<uuid:pk>/download/", views.DocumentViewSet.as_view({"get": "download"}), name="document-download"),
]
