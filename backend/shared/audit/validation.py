import uuid
from django.conf import settings
from django.db import models


class ValidationTrace(models.Model):
    class ValidationType(models.TextChoices):
        APPROVE = "APPROVE", "Approbation"
        REJECT = "REJECT", "Rejet"
        SIGN = "SIGN", "Signature"
        CERTIFY = "CERTIFY", "Certification"
        VALIDATE = "VALIDATE", "Validation"
        AUDIT = "AUDIT", "Vérification"
        REVIEW = "REVIEW", "Revue"

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvé"
        REJECTED = "REJECTED", "Rejeté"
        CANCELLED = "CANCELLED", "Annulé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    validation_type = models.CharField(max_length=20, choices=ValidationType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="validations_performed",
    )
    validated_by_email = models.EmailField(blank=True)
    validated_by_role = models.CharField(max_length=20, blank=True)

    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE,
    )
    object_id = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=500, blank=True)

    comment = models.TextField(blank=True, help_text="Commentaire du validateur")
    evidence = models.JSONField(default=dict, blank=True, help_text="Preuves de validation (documents, métadonnées)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    requires_second_approval = models.BooleanField(default=False, help_text="Nécessite une double validation")
    second_approval_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="second_validations",
    )
    second_approval_at = models.DateTimeField(null=True, blank=True)

    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Date d'expiration de la validation")
    is_expired = models.BooleanField(default=False)

    request_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trace de validation"
        verbose_name_plural = "Traces de validation"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["validated_by", "-created_at"]),
            models.Index(fields=["validation_type", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_validation_type_display()}] {self.object_repr} — {self.get_status_display()}"
