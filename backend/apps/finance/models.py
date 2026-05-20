"""
============================================================
FINANCE MODELS — Architecture comptable professionnelle
============================================================

MODÈLES :
  FiscalYear     → Exercice fiscal (enveloppe annuelle)
  Budget         → Budget par type de prestation / département
  BudgetLine     → Lignes budgétaires détaillées
  Payment        → Paiement d'une prestation (ordre de virement)
  PaymentBatch   → Lot de paiements (virement groupé)
  FinancialEntry → Écriture comptable (journal général)
  FinancialAlert → Alertes automatiques (seuils, anomalies)

PRÉPARATION AI :
  - anomaly_score    → score d'anomalie détecté par le moteur AI
  - variance_percent → écart budget vs réel (feature ML)
  - prediction_data  → JSONField pour les prévisions AI
  - risk_indicators  → indicateurs de risque pour le scoring

SÉCURITÉ FINANCIÈRE :
  - Tous les montants sont en Decimal (pas float → pas d'erreur d'arrondi)
  - Double validation (service + serializer)
  - Audit trail sur chaque mutation
  - Séparation ordonnateur / comptable (permissions)
  - Journal comptable immuable (entries ne peuvent pas être modifiées)
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.models import BaseModel


# ═══════════════════════════════════════════════════════════
# EXERCICE FISCAL
# ═══════════════════════════════════════════════════════════
class FiscalYear(BaseModel):
    """Exercice fiscal annuel — enveloppe budgétaire globale."""

    class Status(models.TextChoices):
        DRAFT    = "draft",    "Brouillon"
        OPEN     = "open",     "Ouvert"
        CLOSED   = "closed",   "Clôturé"
        ARCHIVED = "archived", "Archivé"

    year        = models.PositiveSmallIntegerField(unique=True, verbose_name="Année")
    label       = models.CharField(max_length=100, verbose_name="Libellé")
    start_date  = models.DateField(verbose_name="Date de début")
    end_date    = models.DateField(verbose_name="Date de fin")
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    # Enveloppe globale
    total_budget  = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"),
                                        verbose_name="Budget total (DZD)")
    total_paid    = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"),
                                        verbose_name="Total payé (DZD)")
    total_committed= models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"),
                                         verbose_name="Total engagé (DZD)")

    # Métadonnées
    notes          = models.TextField(blank=True)
    closed_at      = models.DateTimeField(null=True, blank=True)
    closed_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="closed_fiscal_years")

    # AI
    prediction_data = models.JSONField(default=dict, blank=True,
                                       help_text="Prévisions budgétaires AI pour l'année suivante")

    class Meta:
        verbose_name        = "Exercice fiscal"
        verbose_name_plural = "Exercices fiscaux"
        ordering            = ["-year"]

    def __str__(self):
        return f"Exercice {self.year} [{self.get_status_display()}]"

    @property
    def consumption_rate(self) -> Decimal:
        """Taux de consommation budgétaire (%)."""
        if not self.total_budget or self.total_budget == 0:
            return Decimal("0")
        return (self.total_paid / self.total_budget * 100).quantize(Decimal("0.01"))

    @property
    def available_budget(self) -> Decimal:
        return self.total_budget - self.total_paid - self.total_committed

    @property
    def is_active(self) -> bool:
        today = timezone.now().date()
        return self.status == self.Status.OPEN and self.start_date <= today <= self.end_date


# ═══════════════════════════════════════════════════════════
# BUDGET
# ═══════════════════════════════════════════════════════════
class Budget(BaseModel):
    """
    Budget alloué par type de prestation et/ou département
    pour un exercice fiscal donné.
    """

    class Status(models.TextChoices):
        DRAFT    = "draft",    "Brouillon"
        APPROVED = "approved", "Approuvé"
        ACTIVE   = "active",   "Actif"
        CLOSED   = "closed",   "Clôturé"

    fiscal_year  = models.ForeignKey(FiscalYear, on_delete=models.PROTECT,
                                     related_name="budgets", verbose_name="Exercice fiscal")
    benefit_type = models.ForeignKey("benefits.BenefitType", on_delete=models.PROTECT,
                                     null=True, blank=True, related_name="budgets",
                                     verbose_name="Type de prestation")
    department   = models.ForeignKey("departments.Department", on_delete=models.PROTECT,
                                     null=True, blank=True, related_name="budgets",
                                     verbose_name="Département")

    code        = models.CharField(max_length=30, unique=True, verbose_name="Code budget")
    label       = models.CharField(max_length=200, verbose_name="Libellé")
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    # Montants
    allocated_amount  = models.DecimalField(max_digits=15, decimal_places=2,
                                            verbose_name="Montant alloué (DZD)")
    committed_amount  = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"),
                                            verbose_name="Montant engagé (DZD)")
    paid_amount       = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"),
                                            verbose_name="Montant payé (DZD)")
    reserved_amount   = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"),
                                            verbose_name="Montant réservé (DZD)")

    # Alertes
    alert_threshold_pct = models.PositiveSmallIntegerField(
        default=80, verbose_name="Seuil d'alerte (%)",
        help_text="Déclenche une alerte quand la consommation dépasse ce seuil"
    )

    # Approbation
    approved_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="approved_budgets")
    approved_at  = models.DateTimeField(null=True, blank=True)

    notes        = models.TextField(blank=True)

    # AI
    variance_percent = models.FloatField(null=True, blank=True,
                                         help_text="Écart budget vs réel (%) — feature ML")
    anomaly_score    = models.FloatField(null=True, blank=True,
                                         help_text="Score d'anomalie IA (0-100)")
    prediction_data  = models.JSONField(default=dict, blank=True,
                                        help_text="Prévisions et recommandations IA")

    class Meta:
        verbose_name        = "Budget"
        verbose_name_plural = "Budgets"
        ordering            = ["fiscal_year__year", "code"]
        indexes = [
            models.Index(fields=["fiscal_year","status"]),
            models.Index(fields=["benefit_type","fiscal_year"]),
            models.Index(fields=["department","fiscal_year"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["fiscal_year","benefit_type","department"],
                condition=models.Q(department__isnull=False, benefit_type__isnull=False),
                name="unique_budget_per_type_dept_year",
            )
        ]

    def __str__(self):
        return f"[{self.code}] {self.label} — {self.fiscal_year.year}"

    @property
    def available_amount(self) -> Decimal:
        return self.allocated_amount - self.paid_amount - self.committed_amount - self.reserved_amount

    @property
    def consumption_rate(self) -> Decimal:
        if not self.allocated_amount or self.allocated_amount == 0:
            return Decimal("0")
        return ((self.paid_amount + self.committed_amount) / self.allocated_amount * 100).quantize(Decimal("0.01"))

    @property
    def is_alert_triggered(self) -> bool:
        return float(self.consumption_rate) >= self.alert_threshold_pct

    @property
    def is_overrun(self) -> bool:
        return self.available_amount < 0

    def update_totals(self):
        """Recalcule les totaux depuis les paiements réels. Appelé après chaque payment."""
        from django.db.models import Sum
        from apps.finance.models import Payment
        qs = Payment.objects.filter(budget=self, is_deleted=False)
        self.paid_amount      = qs.filter(status="paid").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        self.committed_amount = qs.filter(status__in=["pending","approved"]).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        self.save(update_fields=["paid_amount","committed_amount","updated_at"])


# ═══════════════════════════════════════════════════════════
# LOT DE PAIEMENTS
# ═══════════════════════════════════════════════════════════
class PaymentBatch(BaseModel):
    """
    Lot de paiements groupés — ordre de virement bancaire.
    Regroupe N paiements pour un seul ordre de virement.
    """

    class Status(models.TextChoices):
        DRAFT     = "draft",     "Brouillon"
        SUBMITTED = "submitted", "Soumis"
        APPROVED  = "approved",  "Approuvé"
        SENT      = "sent",      "Envoyé à la banque"
        CONFIRMED = "confirmed", "Confirmé par la banque"
        REJECTED  = "rejected",  "Rejeté"

    reference      = models.CharField(max_length=30, unique=True, editable=False)
    label          = models.CharField(max_length=200, verbose_name="Libellé du lot")
    fiscal_year    = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="batches")
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    payment_method = models.CharField(
        max_length=20,
        choices=[("virement","Virement bancaire"),("cheque","Chèque"),("caisse","Caisse"),("ccp","CCP")],
        default="virement",
        verbose_name="Mode de paiement",
    )

    total_amount   = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    payment_count  = models.PositiveIntegerField(default=0)

    # Dates
    scheduled_date  = models.DateField(null=True, blank=True, verbose_name="Date d'exécution prévue")
    executed_date   = models.DateField(null=True, blank=True, verbose_name="Date d'exécution réelle")
    bank_reference  = models.CharField(max_length=100, blank=True, verbose_name="Référence bancaire")

    # Approbation
    submitted_by    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="submitted_batches")
    approved_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="approved_batches")
    approved_at     = models.DateTimeField(null=True, blank=True)

    notes          = models.TextField(blank=True)
    class Meta:
        verbose_name        = "Lot de paiements"
        verbose_name_plural = "Lots de paiements"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.total_amount:,.0f} DZD ({self.payment_count} paiements)"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._gen_ref()
        super().save(*args, **kwargs)

    @classmethod
    def _gen_ref(cls):
        year   = timezone.now().year
        prefix = f"LOT-{year}-"
        last   = cls.all_objects.filter(reference__startswith=prefix).order_by("-reference").first()
        num    = int(last.reference.rsplit("-",1)[-1]) + 1 if last else 1
        return f"{prefix}{num:04d}"

    def recalculate(self):
        from django.db.models import Sum, Count
        agg = self.payments.filter(is_deleted=False).aggregate(
            total=Sum("amount"), count=Count("id")
        )
        self.total_amount  = agg["total"] or Decimal("0")
        self.payment_count = agg["count"] or 0
        self.save(update_fields=["total_amount","payment_count","updated_at"])


# ═══════════════════════════════════════════════════════════
# PAIEMENT
# ═══════════════════════════════════════════════════════════
class Payment(BaseModel):
    """
    Ordre de paiement pour une prestation validée.
    Lié à une prestation, un budget, et optionnellement un lot.

    RÈGLE COMPTABLE : Un paiement ne peut être modifié qu'en état 'pending'.
    Une fois 'paid', il est immuable (créer une écriture de correction).
    """

    class Status(models.TextChoices):
        PENDING   = "pending",   "En attente"
        APPROVED  = "approved",  "Approuvé"
        PROCESSING= "processing","En traitement"
        PAID      = "paid",      "Payé"
        FAILED    = "failed",    "Échoué"
        CANCELLED = "cancelled", "Annulé"
        REVERSED  = "reversed",  "Annulé par écriture inverse"

    reference  = models.CharField(max_length=30, unique=True, editable=False)
    benefit    = models.OneToOneField("benefits.Benefit", on_delete=models.PROTECT,
                                      related_name="payment_record", verbose_name="Prestation")
    budget     = models.ForeignKey(Budget, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="payments", verbose_name="Budget")
    batch      = models.ForeignKey(PaymentBatch, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="payments", verbose_name="Lot de paiement")
    fiscal_year= models.ForeignKey(FiscalYear, on_delete=models.PROTECT,
                                   related_name="payments", verbose_name="Exercice")

    # Bénéficiaire
    employee        = models.ForeignKey("employees.Employee", on_delete=models.PROTECT,
                                        related_name="payments", verbose_name="Employé")
    beneficiary_name= models.CharField(max_length=200, blank=True, verbose_name="Nom bénéficiaire")

    # Montants
    amount          = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant (DZD)")
    fees            = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"),
                                          verbose_name="Frais bancaires (DZD)")
    net_amount      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"),
                                          verbose_name="Montant net (DZD)")

    status          = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    payment_method  = models.CharField(
        max_length=20,
        choices=[("virement","Virement"),("cheque","Chèque"),("caisse","Caisse"),("ccp","CCP")],
        default="virement",
    )

    # Informations bancaires
    bank_account    = models.CharField(max_length=50, blank=True, verbose_name="RIB / CCP")
    bank_name       = models.CharField(max_length=100, blank=True, verbose_name="Banque")
    bank_reference  = models.CharField(max_length=100, blank=True, verbose_name="Référence bancaire")

    # Dates
    scheduled_date  = models.DateField(null=True, blank=True, verbose_name="Date d'exécution prévue")
    executed_date   = models.DateField(null=True, blank=True, verbose_name="Date d'exécution réelle")
    value_date      = models.DateField(null=True, blank=True, verbose_name="Date de valeur")

    # Approbation
    approved_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="approved_payments")
    approved_at     = models.DateTimeField(null=True, blank=True)

    # Comptabilité
    accounting_entry= models.CharField(max_length=50, blank=True, verbose_name="N° écriture comptable")
    cost_center     = models.CharField(max_length=50, blank=True, verbose_name="Centre de coût")

    notes           = models.TextField(blank=True)

    # AI
    anomaly_flag    = models.BooleanField(default=False, help_text="Anomalie détectée par l'IA")
    anomaly_score   = models.FloatField(null=True, blank=True, help_text="Score d'anomalie (0-100)")
    risk_indicators = models.JSONField(default=dict, blank=True, help_text="Indicateurs de risque IA")

    class Meta:
        verbose_name        = "Paiement"
        verbose_name_plural = "Paiements"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["employee","status"]),
            models.Index(fields=["budget","status"]),
            models.Index(fields=["fiscal_year","status"]),
            models.Index(fields=["executed_date"]),
            models.Index(fields=["anomaly_flag"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.employee} — {self.amount:,.0f} DZD [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._gen_ref()
        self.net_amount = self.amount - self.fees
        # Dénormaliser le nom de l'employé pour le bénéficiaire
        if not self.beneficiary_name and self.employee_id:
            try:
                self.beneficiary_name = self.employee.get_full_name()
            except Exception:
                pass
        super().save(*args, **kwargs)

    @classmethod
    def _gen_ref(cls):
        year   = timezone.now().year
        prefix = f"PAY-{year}-"
        last   = cls.all_objects.filter(reference__startswith=prefix).order_by("-reference").first()
        num    = int(last.reference.rsplit("-",1)[-1]) + 1 if last else 1
        return f"{prefix}{num:05d}"

    def can_be_modified(self) -> bool:
        return self.status in (self.Status.PENDING, self.Status.FAILED)

    def can_be_cancelled(self) -> bool:
        return self.status not in (self.Status.PAID, self.Status.REVERSED)


# ═══════════════════════════════════════════════════════════
# ÉCRITURE COMPTABLE
# ═══════════════════════════════════════════════════════════
class FinancialEntry(BaseModel):
    """
    Écriture comptable du journal général.
    IMMUABLE par design (principe comptable fondamental).
    Les corrections se font par écritures inverses, jamais par modification.
    """

    class EntryType(models.TextChoices):
        DEBIT      = "debit",      "Débit"
        CREDIT     = "credit",     "Crédit"
        ADJUSTMENT = "adjustment", "Ajustement"
        REVERSAL   = "reversal",   "Annulation (écriture inverse)"
        OPENING    = "opening",    "À-nouveau d'ouverture"
        CLOSING    = "closing",    "Clôture"

    fiscal_year     = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="entries")
    payment         = models.ForeignKey(Payment, on_delete=models.PROTECT, null=True, blank=True,
                                        related_name="accounting_entries")
    budget          = models.ForeignKey(Budget,  on_delete=models.PROTECT, null=True, blank=True,
                                        related_name="accounting_entries")

    entry_number    = models.CharField(max_length=30, unique=True, editable=False, verbose_name="N° écriture")
    entry_type      = models.CharField(max_length=15, choices=EntryType.choices)
    label           = models.CharField(max_length=300, verbose_name="Libellé")
    amount          = models.DecimalField(max_digits=18, decimal_places=2)
    entry_date      = models.DateField(default=timezone.now, verbose_name="Date d'écriture")
    accounting_date = models.DateField(default=timezone.now, verbose_name="Date comptable")

    # Comptes comptables (pour future intégration ERP)
    debit_account   = models.CharField(max_length=20, blank=True, verbose_name="Compte débité")
    credit_account  = models.CharField(max_length=20, blank=True, verbose_name="Compte crédité")

    # Référence à l'écriture annulée (si reversal)
    reversed_entry  = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name="reversals", verbose_name="Écriture annulée")
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, related_name="accounting_entries")
    notes           = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering            = ["-entry_date", "-entry_number"]
        indexes = [
            models.Index(fields=["fiscal_year","entry_date"]),
            models.Index(fields=["entry_type"]),
            models.Index(fields=["payment"]),
        ]

    def __str__(self):
        return f"{self.entry_number} — {self.label} — {self.amount:,.0f} DZD"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            self.entry_number = self._gen_number()
        if not self._state.adding:
            raise PermissionError("Les écritures comptables sont immuables. Créez une écriture d'annulation.")
        super().save(*args, **kwargs)

    @classmethod
    def _gen_number(cls):
        year   = timezone.now().year
        prefix = f"ECR-{year}-"
        last   = cls.objects.filter(entry_number__startswith=prefix).order_by("-entry_number").first()
        num    = int(last.entry_number.rsplit("-",1)[-1]) + 1 if last else 1
        return f"{prefix}{num:06d}"


# ═══════════════════════════════════════════════════════════
# ALERTE FINANCIÈRE
# ═══════════════════════════════════════════════════════════
class FinancialAlert(BaseModel):
    """
    Alertes automatiques générées par le système.
    Préparation pour le moteur d'alertes AI.
    """

    class AlertType(models.TextChoices):
        BUDGET_THRESHOLD  = "budget_threshold",  "Seuil budgétaire atteint"
        BUDGET_OVERRUN    = "budget_overrun",     "Dépassement budgétaire"
        ANOMALY_DETECTED  = "anomaly_detected",   "Anomalie détectée"
        LARGE_PAYMENT     = "large_payment",      "Paiement élevé"
        DUPLICATE_PAYMENT = "duplicate_payment",  "Doublon potentiel"
        FISCAL_YEAR_END   = "fiscal_year_end",    "Fin d'exercice proche"
        SLA_BREACH        = "sla_breach",         "Dépassement délai SLA"

    class Severity(models.TextChoices):
        INFO     = "info",     "Information"
        WARNING  = "warning",  "Avertissement"
        CRITICAL = "critical", "Critique"

    alert_type   = models.CharField(max_length=25, choices=AlertType.choices)
    severity     = models.CharField(max_length=10, choices=Severity.choices, default=Severity.WARNING)
    title        = models.CharField(max_length=200)
    message      = models.TextField()
    is_read      = models.BooleanField(default=False)
    is_resolved  = models.BooleanField(default=False)
    resolved_at  = models.DateTimeField(null=True, blank=True)
    resolved_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="resolved_alerts")

    # Référence à l'objet concerné
    fiscal_year  = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, null=True, blank=True)
    budget       = models.ForeignKey(Budget,     on_delete=models.CASCADE, null=True, blank=True)
    payment      = models.ForeignKey(Payment,    on_delete=models.CASCADE, null=True, blank=True)

    # Données AI
    ai_generated  = models.BooleanField(default=False, help_text="Générée par le moteur AI")
    ai_confidence = models.FloatField(null=True, blank=True, help_text="Confiance du modèle AI (0-1)")
    metadata      = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name        = "Alerte financière"
        verbose_name_plural = "Alertes financières"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["severity","is_resolved"]),
            models.Index(fields=["alert_type","is_resolved"]),
            models.Index(fields=["fiscal_year","is_resolved"]),
        ]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"
