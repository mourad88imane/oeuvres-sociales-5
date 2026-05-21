"""
============================================================
BENEFITS MODELS — Prestations sociales
============================================================

BenefitType  → Types de prestations configurables
BenefitAttachment → Pièces jointes
Benefit      → Demande de prestation (porte le workflow)
BenefitComment → Commentaires des intervenants

PRÉPARATION AI :
  - analytics_data JSONField → stockage features ML
  - ai_score, ai_anomaly_flag → résultats futurs du moteur AI
  - risk_score → scoring du risque de la demande
"""

import os
import uuid

from apps.benefits.workflow import benefit_workflow
from core.models import BaseModel
from django.conf import settings
from django.db import models
from django.utils import timezone
from shared.workflow.models import WorkflowMixin


def attachment_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return os.path.join(
        "benefits", "attachments", str(instance.benefit.id), f"{uuid.uuid4().hex}.{ext}"
    )


# ═══════════════════════════════════════════════════════════
# TYPE DE PRESTATION
# ═══════════════════════════════════════════════════════════
class BenefitType(BaseModel):
    class Category(models.TextChoices):
        MEDICAL = "medical", "Prise en charge médicale"
        LOAN = "loan", "Prêt"
        PURCHASE = "purchase", "Achat facilité"
        BONUS = "bonus", "Prime"
        AID = "aid", "Aide exceptionnelle"
        OTHER = "other", "Autre"

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    name = models.CharField(max_length=150, verbose_name="Libellé")
    category = models.CharField(max_length=20, choices=Category.choices, verbose_name="Catégorie")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Plafonds et règles d'éligibilité
    max_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Montant plafond (DZD)"
    )
    min_seniority_years = models.FloatField(
        null=True, blank=True, verbose_name="Ancienneté minimale (années)"
    )
    max_per_year = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nb max par an et par employé"
    )
    requires_attachments = models.BooleanField(
        default=False, verbose_name="Pièces justificatives obligatoires"
    )
    required_attachments_description = models.TextField(
        blank=True, verbose_name="Description des pièces requises"
    )

    # Délai de traitement cible (pour analytics/SLA)
    target_processing_days = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Délai cible (jours)"
    )

    # AI
    ai_processing_hints = models.JSONField(
        default=dict, blank=True, verbose_name="Hints pour le moteur AI futur"
    )

    class Meta:
        verbose_name = "Type de prestation"
        verbose_name_plural = "Types de prestations"
        ordering = ["category", "name"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["category", "is_active"])]

    def __str__(self):
        return f"[{self.code}] {self.name}"


# ═══════════════════════════════════════════════════════════
# DEMANDE DE PRESTATION
# ═══════════════════════════════════════════════════════════
class Benefit(WorkflowMixin, BaseModel):
    """
    Demande de prestation — porte le workflow métier.
    Intègre WorkflowMixin pour les champs d'état.
    """

    workflow_definition = benefit_workflow

    # ── Référence ─────────────────────────────────────────
    reference = models.CharField(
        max_length=30, unique=True, editable=False, verbose_name="Référence"
    )

    # ── Acteurs ───────────────────────────────────────────
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="benefits",
        verbose_name="Employé",
    )
    benefit_type = models.ForeignKey(
        BenefitType,
        on_delete=models.PROTECT,
        related_name="benefits",
        verbose_name="Type de prestation",
    )
    beneficiary = models.ForeignKey(
        "beneficiaries.Beneficiary",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benefits",
        verbose_name="Ayant droit concerné",
    )

    # ── Montants ──────────────────────────────────────────
    requested_amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant demandé (DZD)"
    )
    approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant approuvé (DZD)",
    )
    paid_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Montant payé (DZD)"
    )

    # ── Description ───────────────────────────────────────
    title = models.CharField(max_length=200, verbose_name="Objet de la demande")
    description = models.TextField(blank=True, verbose_name="Description / Justification")
    priority = models.CharField(
        max_length=10,
        choices=[("low", "Basse"), ("normal", "Normale"), ("high", "Haute"), ("urgent", "Urgente")],
        default="normal",
        verbose_name="Priorité",
    )

    # ── Dates workflow ────────────────────────────────────
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de soumission")
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de rejet")
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance souhaitée")

    # ── Acteurs workflow ──────────────────────────────────
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_benefits",
        verbose_name="Validé par",
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paid_benefits",
        verbose_name="Payé par",
    )

    # ── Données de rejet ──────────────────────────────────
    rejection_reason = models.TextField(blank=True, verbose_name="Motif de rejet")

    # ── Paiement ──────────────────────────────────────────
    payment_reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence de paiement"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("virement", "Virement bancaire"),
            ("cheque", "Chèque"),
            ("caisse", "Caisse"),
            ("ccp", "CCP"),
        ],
        blank=True,
        verbose_name="Mode de paiement",
    )

    # ── Analytics & AI (préparation) ──────────────────────
    analytics_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données analytiques",
        help_text="Timestamps et durées par état — dataset ML",
    )
    ai_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score AI",
        help_text="Score de la demande calculé par le moteur AI",
    )
    ai_anomaly_flag = models.BooleanField(
        default=False,
        verbose_name="Anomalie détectée AI",
        help_text="True si le moteur AI a détecté une anomalie",
    )
    risk_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de risque",
        help_text="Score de risque calculé (0-100)",
    )
    ai_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées AI",
        help_text="Résultats et recommandations du moteur AI",
    )

    # Notes internes
    internal_notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["workflow_state"]),
            models.Index(fields=["employee", "workflow_state"]),
            models.Index(fields=["benefit_type", "workflow_state"]),
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["priority", "workflow_state"]),
            models.Index(fields=["ai_anomaly_flag"]),  # Pour dashboard AI
        ]

    def __str__(self):
        return f"{self.reference} — {self.benefit_type.name} — {self.workflow_state_label}"

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
        prefix = f"PREST-{year}-"
        last = cls.all_objects.filter(reference__startswith=prefix).order_by("-reference").first()
        num = 1
        if last:
            try:
                num = int(last.reference.rsplit("-", 1)[-1]) + 1
            except ValueError:
                pass
        return f"{prefix}{num:05d}"

    @property
    def is_overdue(self) -> bool:
        """Dépasse la date d'échéance souhaitée."""
        if not self.due_date:
            return False
        from datetime import date

        return date.today() > self.due_date and self.workflow_state not in (
            "paid",
            "rejected",
            "cancelled",
        )

    @property
    def processing_days(self) -> int | None:
        """Nombre de jours depuis la soumission."""
        if not self.submitted_at:
            return None
        delta = timezone.now() - self.submitted_at
        return delta.days

    @property
    def amount_display(self) -> str:
        amt = self.approved_amount or self.requested_amount
        return f"{amt:,.0f} DZD" if amt else "—"

    @property
    def attachments_count(self) -> int:
        return self.attachments.filter(is_deleted=False).count()


# ═══════════════════════════════════════════════════════════
# PIÈCES JOINTES
# ═══════════════════════════════════════════════════════════
class BenefitAttachment(BaseModel):
    class DocType(models.TextChoices):
        PRESCRIPTION = "prescription", "Ordonnance médicale"
        INVOICE = "invoice", "Facture"
        CERTIFICATE = "certificate", "Certificat"
        IDENTITY = "identity", "Pièce d'identité"
        SALARY_SLIP = "salary_slip", "Bulletin de salaire"
        BANK_DETAILS = "bank_details", "RIB bancaire"
        OTHER = "other", "Autre document"

    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_path, verbose_name="Fichier")
    original_name = models.CharField(max_length=255, verbose_name="Nom original du fichier")
    doc_type = models.CharField(
        max_length=20,
        choices=DocType.choices,
        default=DocType.OTHER,
        verbose_name="Type de document",
    )
    description = models.CharField(max_length=300, blank=True, verbose_name="Description")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (octets)")
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_attachments",
    )

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.original_name} → {self.benefit.reference}"

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


# ═══════════════════════════════════════════════════════════
# COMMENTAIRES
# ═══════════════════════════════════════════════════════════
class BenefitComment(BaseModel):
    class CommentType(models.TextChoices):
        INTERNAL = "internal", "Note interne"
        REQUESTER = "requester", "Message au demandeur"
        SYSTEM = "system", "Message système"

    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="benefit_comments",
    )
    comment_type = models.CharField(
        max_length=15, choices=CommentType.choices, default=CommentType.INTERNAL
    )
    content = models.TextField(verbose_name="Contenu")
    # Lié à une transition spécifique (optionnel)
    workflow_state_at_time = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.comment_type}] {self.benefit.reference} — {self.author}"
