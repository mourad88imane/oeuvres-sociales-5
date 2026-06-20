import os
import uuid

from core.models import BaseModel
from django.conf import settings
from django.db import models
from django.utils import timezone
from shared.workflow.models import WorkflowMixin

from .workflow import loan_workflow


def attachment_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return os.path.join(
        "loans", "attachments", str(instance.loan.id), f"{uuid.uuid4().hex}.{ext}"
    )


class Loan(WorkflowMixin, BaseModel):
    workflow_definition = loan_workflow

    reference = models.CharField(
        max_length=30, unique=True, editable=False, verbose_name="Référence"
    )

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="loans",
        verbose_name="Employé",
    )

    requested_amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant demandé (DZD)"
    )
    approved_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Montant approuvé (DZD)",
    )
    paid_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Montant payé (DZD)",
    )

    monthly_instalment = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Mensualité (DZD)",
    )
    instalment_count = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nombre de mensualités"
    )

    reason = models.TextField(verbose_name="Motif du prêt")
    description = models.TextField(blank=True, verbose_name="Observations")

    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de soumission")
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de rejet")

    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="validated_loans", verbose_name="Validé par",
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="paid_loans", verbose_name="Payé par",
    )

    rejection_reason = models.TextField(blank=True, verbose_name="Motif de rejet")
    payment_reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence de paiement"
    )

    class Meta:
        verbose_name = "Prêt"
        verbose_name_plural = "Prêts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["workflow_state"]),
            models.Index(fields=["employee", "workflow_state"]),
            models.Index(fields=["submitted_at"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.employee.get_full_name()} — {self.workflow_state_label}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        if not self.workflow_state:
            self.workflow_state = "draft"
        super().save(*args, **kwargs)

    @classmethod
    def _generate_reference(cls):
        from django.utils import timezone as tz
        year = tz.now().year
        prefix = f"PRET-{year}-"
        last = cls.all_objects.filter(reference__startswith=prefix).order_by("-reference").first()
        num = 1
        if last:
            try:
                num = int(last.reference.rsplit("-", 1)[-1]) + 1
            except ValueError:
                pass
        return f"{prefix}{num:05d}"

    @property
    def amount_display(self) -> str:
        amt = self.approved_amount or self.requested_amount
        return f"{amt:,.0f} DZD" if amt else "—"

    @property
    def instalment_display(self) -> str:
        if self.monthly_instalment and self.instalment_count:
            return f"{self.monthly_instalment:,.0f} DZD × {self.instalment_count} mois"
        return "—"


class LoanAttachment(BaseModel):
    class DocType(models.TextChoices):
        CONTRACT = "contract", "Contrat de prêt"
        IDENTITY = "identity", "Pièce d'identité"
        SALARY_SLIP = "salary_slip", "Bulletin de salaire"
        BANK_DETAILS = "bank_details", "RIB bancaire"
        OTHER = "other", "Autre"

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_path, verbose_name="Fichier")
    original_name = models.CharField(max_length=255, verbose_name="Nom original")
    doc_type = models.CharField(
        max_length=20, choices=DocType.choices, default=DocType.OTHER,
        verbose_name="Type de document",
    )
    description = models.CharField(max_length=300, blank=True, verbose_name="Description")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (octets)")
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name="uploaded_loan_attachments",
    )

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.original_name} → {self.loan.reference}"

    @property
    def file_size_display(self) -> str:
        s = self.file_size
        for unit in ("o", "Ko", "Mo", "Go"):
            if s < 1024:
                return f"{s:.1f} {unit}"
            s /= 1024
        return f"{s:.1f} To"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)


class LoanComment(BaseModel):
    class CommentType(models.TextChoices):
        INTERNAL = "internal", "Note interne"
        REQUESTER = "requester", "Message au demandeur"
        SYSTEM = "system", "Message système"

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name="loan_comments",
    )
    comment_type = models.CharField(
        max_length=15, choices=CommentType.choices, default=CommentType.INTERNAL
    )
    content = models.TextField(verbose_name="Contenu")
    workflow_state_at_time = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.comment_type}] {self.loan.reference} — {self.author}"
