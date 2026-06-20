from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    time_ago = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "title", "description", "category", "category_display",
            "file", "file_name", "file_size_bytes", "file_type", "tags",
            "is_deleted", "uploaded_by", "related_entity_type", "related_entity_id",
            "download_url", "time_ago", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "uploaded_by"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)

    def get_download_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=Document.Category.choices, default="general")
    tags = serializers.JSONField(default=list, required=False)
    related_entity_type = serializers.CharField(required=False, allow_blank=True, max_length=50)
    related_entity_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    file = serializers.FileField(required=True)
