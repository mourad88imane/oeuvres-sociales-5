import os
import uuid

from django.conf import settings
from django.db import models


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f"documents/{instance.category}/{instance.pk}{ext}"


class Document(models.Model):

    class Category(models.TextChoices):
        GENERAL = "general", "Général"
        CONTRACT = "contract", "Contrat"
        REPORT = "report", "Rapport"
        INVOICE = "invoice", "Facture"
        MEDICAL = "medical", "Médical"
        ADMIN = "admin", "Administratif"
        OTHER = "other", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_deleted = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["is_deleted"]),
        ]

    def __str__(self):
        return self.title or self.file_name or str(self.id)
