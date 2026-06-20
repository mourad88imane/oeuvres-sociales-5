import mimetypes
import os

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.http import FileResponse
from django.utils.translation import gettext as _

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.filter(is_deleted=False)
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "file_type"]
    search_fields = ["title", "description", "tags"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

    @action(detail=False, methods=["post"])
    def upload(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        file_name = file.name
        file_type = mimetypes.guess_type(file_name)[0] or os.path.splitext(file_name)[1]

        doc = Document.objects.create(
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            category=serializer.validated_data.get("category", "general"),
            file=file,
            file_name=file_name,
            file_size_bytes=file.size,
            file_type=file_type or "",
            tags=serializer.validated_data.get("tags", []),
            related_entity_type=serializer.validated_data.get("related_entity_type", ""),
            related_entity_id=serializer.validated_data.get("related_entity_id", ""),
            uploaded_by=request.user if request.user.is_authenticated else None,
        )

        doc_serializer = DocumentSerializer(doc)
        return Response({"status": "success", "data": doc_serializer.data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        return Response({
            "status": "success",
            "data": [{"value": c[0], "label": c[1]} for c in Document.Category.choices],
        })

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        doc = self.get_object()
        if not doc.file:
            return Response({"status": "error", "message": "Fichier non trouvé"}, status=404)
        return FileResponse(doc.file, as_attachment=True, filename=doc.file_name)
