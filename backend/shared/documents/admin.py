from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "file_type", "file_size_bytes", "uploaded_by", "created_at"]
    list_filter = ["category", "file_type"]
    search_fields = ["title", "description", "tags"]
