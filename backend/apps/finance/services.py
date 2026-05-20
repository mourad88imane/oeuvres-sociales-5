"""
============================================================
FINANCE SERVICE — Logique métier financière
============================================================
Toutes les opérations financières passent par ce service.
RÈGLES COMPTABLES FONDAMENTALES :
  1. Double entry : toute opération génère une écriture comptable
  2. Immuabilité : les paiements payés ne peuvent être modifiés
  3. Séparation ordonnateur/comptable (validé par les permissions)
  4. Validation montants : Decimal obligatoire, jamais float
  5. Alertes automatiques sur seuils budgétaires
"""
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone

from shared.audit.services import AuditService
from .models import (
    Budget, FinancialAlert, FinancialEntry,
    FiscalYear, Payment, PaymentBatch,
)

logger = logging.getLogger("apps.finance")
audit  = AuditService()


class FinanceValidationError(Exception):
    def __init__(self, message: str, code: str = "FINANCE_ERROR"):
        self.message = message
        self.code    = code
        super().__init__(message)


class FiscalYearService:
    """Gestion des exercices fiscaux."""

    def get_active_year(self) -> Optional[FiscalYear]:
        today = timezone.now().date()
        return FiscalYear.objects.filter(
            status=FiscalYear.Status.OPEN,
            start_date__lte=today,
            end_date__gte=today,
        ).first()

    @transaction.atomic
    def create(self, data: dict, user=None, request=None) -> FiscalYear:
        fy = FiscalYear(**data)
        if user:
            fy.created_by = user
            fy.updated_by = user
        fy.save()
        audit.log_create(user=user, obj=fy, request=request)
        return fy

    @transaction.atomic
    def open(self, fy: FiscalYear, user=None) -> FiscalYear:
        if fy.status not in (FiscalYear.Status.DRAFT,):
            raise FinanceValidationError("Seul un exercice en brouillon peut être ouvert.")
        fy.status = FiscalYear.Status.OPEN
        fy.save(update_fields=["status", "updated_at"])
        audit.log_action(action="UPDATE", user=user, obj=fy,
                         extra_data={"action": "open"}, severity="HIGH")
        logger.info(f"Fiscal year {fy.year} opened by {user}")
        return fy

    @transaction.atomic
    def close(self, fy: FiscalYear, user=None) -> FiscalYear:
        if fy.status != FiscalYear.Status.OPEN:
            raise FinanceValidationError("Seul un exercice ouvert peut être clôturé.")
        # Vérifier qu'il n'y a pas de paiements en attente
        pending = Payment.objects.filter(
            fiscal_year=fy,
            status__in=[Payment.Status.PENDING, Payment.Status.APPROVED, Payment.Status.PROCESSING],
            is_deleted=False,
        ).count()
        if pending:
            raise FinanceValidationError(
                f"Impossible de clôturer : {pending} paiement(s) en attente.",
                "PENDING_PAYMENTS"
            )
        fy.status     = FiscalYear.Status.CLOSED
        fy.closed_at  = timezone.now()
        fy.closed_by  = user
        fy.save(update_fields=["status", "closed_at", "closed_by", "updated_at"])
        audit.log_action(action="UPDATE", user=user, obj=fy,
                         extra_data={"action": "close"}, severity="CRITICAL")
        return fy


class BudgetService:
    """Gestion des budgets."""

    def get_queryset(self):
        return Budget.objects.select_related(
            "fiscal_year", "benefit_type", "department", "approved_by"
        ).filter(is_deleted=False)

    @transaction.atomic
    def create(self, data: dict, user=None, request=None) -> Budget:
        amount = data.get("allocated_amount", Decimal("0"))
        if amount <= 0:
            raise FinanceValidationError("Le montant alloué doit être positif.")
        fy = data.get("fiscal_year")
        if fy and fy.status != FiscalYear.Status.OPEN:
            raise FinanceValidationError(
                "Le budget doit être associé à un exercice fiscal ouvert.",
                "FISCAL_YEAR_NOT_OPEN",
            )
        budget = Budget(**data)
        if user:
            budget.created_by = user
            budget.updated_by = user
        budget.save()
        audit.log_create(user=user, obj=budget, request=request)
        return budget

    @transaction.atomic
    def approve(self, budget: Budget, user=None) -> Budget:
        if budget.status not in (Budget.Status.DRAFT,):
            raise FinanceValidationError("Seul un budget en brouillon peut être approuvé.")
        budget.status      = Budget.Status.APPROVED
        budget.approved_by = user
        budget.approved_at = timezone.now()
        budget.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        audit.log_action(action="APPROVE", user=user, obj=budget, severity="HIGH")
        return budget

    @transaction.atomic
    def update(self, budget: Budget, data: dict, user=None, request=None) -> Budget:
        if budget.status == Budget.Status.CLOSED:
            raise FinanceValidationError("Un budget clôturé ne peut pas être modifié.")
        from django.forms.models import model_to_dict
        before = model_to_dict(budget)
        for k, v in data.items():
            setattr(budget, k, v)
        if user:
            budget.updated_by = user
        budget.save()
        audit.log_update(user=user, obj=budget, before_data=before, request=request)
        return budget

    def get_consumption_report(self, fiscal_year_id: str) -> list:
        """Rapport de consommation budgétaire par type de prestation."""
        budgets = Budget.objects.filter(
            fiscal_year_id=fiscal_year_id, is_deleted=False
        ).select_related("benefit_type", "department")
        return [
            {
                "id":               str(b.id),
                "code":             b.code,
                "label":            b.label,
                "benefit_type":     b.benefit_type.name if b.benefit_type else None,
                "department":       b.department.name   if b.department   else None,
                "allocated":        float(b.allocated_amount),
                "paid":             float(b.paid_amount),
                "committed":        float(b.committed_amount),
                "available":        float(b.available_amount),
                "consumption_rate": float(b.consumption_rate),
                "is_alert":         b.is_alert_triggered,
                "is_overrun":       b.is_overrun,
                "status":           b.status,
            }
            for b in budgets
        ]

    def check_budget_availability(self, budget: Budget, amount: Decimal) -> tuple[bool, str]:
        """Vérifie si le budget dispose des fonds nécessaires."""
        if budget.status not in (Budget.Status.APPROVED, Budget.Status.ACTIVE):
            return False, "Le budget n'est pas actif."
        if amount > budget.available_amount:
            return False, (
                f"Budget insuffisant. Disponible: {budget.available_amount:,.0f} DZD, "
                f"Demandé: {amount:,.0f} DZD."
            )
        return True, ""


class PaymentService:
    """Gestion des paiements — opérations financières sécurisées."""

    def get_queryset(self):
        return Payment.objects.select_related(
            "benefit", "benefit__benefit_type",
            "employee", "employee__department",
            "budget", "fiscal_year", "batch",
            "approved_by",
        ).filter(is_deleted=False)

    def search(self, queryset, search="", status="", fiscal_year_id="",
               budget_id="", employee_id="", department_id="",
               date_from="", date_to="", anomaly_only=False, ordering="-created_at"):
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__matricule__icontains=search) |
                Q(bank_reference__icontains=search)
            )
        if status:          queryset = queryset.filter(status=status)
        if fiscal_year_id:  queryset = queryset.filter(fiscal_year_id=fiscal_year_id)
        if budget_id:       queryset = queryset.filter(budget_id=budget_id)
        if employee_id:     queryset = queryset.filter(employee_id=employee_id)
        if department_id:   queryset = queryset.filter(employee__department_id=department_id)
        if date_from:       queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:         queryset = queryset.filter(created_at__date__lte=date_to)
        if anomaly_only:    queryset = queryset.filter(anomaly_flag=True)
        allowed = {"-created_at","created_at","-amount","amount",
                   "-executed_date","executed_date","status","-status","reference"}
        if ordering in allowed:
            queryset = queryset.order_by(ordering)
        return queryset

    @transaction.atomic
    def create_from_benefit(self, benefit, budget: Budget = None,
                            fiscal_year: FiscalYear = None,
                            user=None, request=None) -> Payment:
        """
        Crée un paiement depuis une prestation validée.
        Vérifie la disponibilité budgétaire avant création.
        """
        # Vérifications de base
        if benefit.workflow_state != "validated":
            raise FinanceValidationError(
                "Seules les prestations validées peuvent générer un paiement.",
                "INVALID_BENEFIT_STATE",
            )
        # Vérifier doublon
        if Payment.objects.filter(benefit=benefit, is_deleted=False).exists():
            raise FinanceValidationError(
                "Un paiement existe déjà pour cette prestation.",
                "DUPLICATE_PAYMENT",
            )
        amount = benefit.approved_amount or benefit.requested_amount
        # Vérification budgétaire
        if budget:
            ok, msg = BudgetService().check_budget_availability(budget, amount)
            if not ok:
                raise FinanceValidationError(msg, "BUDGET_INSUFFICIENT")

        # Exercice fiscal actif
        if not fiscal_year:
            fiscal_year = FiscalYearService().get_active_year()
            if not fiscal_year:
                raise FinanceValidationError("Aucun exercice fiscal actif.", "NO_FISCAL_YEAR")

        payment = Payment(
            benefit=benefit, budget=budget, fiscal_year=fiscal_year,
            employee=benefit.employee,
            amount=amount, status=Payment.Status.PENDING,
            payment_method=benefit.payment_method or "virement",
            bank_account=benefit.employee.bank_account or "",
        )
        if user:
            payment.created_by = user
            payment.updated_by = user
        payment.save()

        # Réserver le montant dans le budget
        if budget:
            budget.reserved_amount += amount
            budget.save(update_fields=["reserved_amount", "updated_at"])

        # Créer l'écriture comptable d'engagement
        self._create_entry(
            payment=payment,
            entry_type=FinancialEntry.EntryType.DEBIT,
            label=f"Engagement prestation {benefit.reference} — {benefit.employee.get_full_name()}",
            amount=amount, user=user,
        )

        audit.log_create(user=user, obj=payment, request=request)
        self._check_and_create_alerts(payment)
        return payment

    @transaction.atomic
    def approve(self, payment: Payment, user=None, request=None) -> Payment:
        if payment.status != Payment.Status.PENDING:
            raise FinanceValidationError("Seul un paiement en attente peut être approuvé.")
        payment.status      = Payment.Status.APPROVED
        payment.approved_by = user
        payment.approved_at = timezone.now()
        payment.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        fy = payment.fiscal_year
        fy.total_committed += payment.amount
        fy.save(update_fields=["total_committed", "updated_at"])
        audit.log_action(action="APPROVE", user=user, obj=payment,
                         request=request, severity="HIGH")
        return payment

    @transaction.atomic
    def mark_paid(self, payment: Payment, bank_reference: str,
                  executed_date=None, paid_amount: Decimal = None,
                  user=None, request=None) -> Payment:
        """Marque le paiement comme effectué et génère l'écriture de règlement."""
        if payment.status != Payment.Status.APPROVED:
            raise FinanceValidationError(
                "Seul un paiement approuvé peut être marqué comme payé.",
                "INVALID_STATUS",
            )
        if not bank_reference.strip():
            raise FinanceValidationError("La référence bancaire est obligatoire.", "REF_REQUIRED")

        final_amount   = paid_amount or payment.amount
        payment.status = Payment.Status.PAID
        payment.bank_reference  = bank_reference
        payment.executed_date   = executed_date or timezone.now().date()
        payment.value_date      = timezone.now().date()
        if user:
            payment.updated_by = user
        payment.save(update_fields=[
            "status","bank_reference","executed_date","value_date","updated_at","updated_by"
        ])

        # Libérer la réservation budgétaire
        if payment.budget:
            budget = payment.budget
            budget.reserved_amount = max(Decimal("0"), budget.reserved_amount - payment.amount)
            budget.save(update_fields=["reserved_amount", "updated_at"])
            budget.update_totals()

        # Mise à jour de l'exercice fiscal
        fy = payment.fiscal_year
        fy.total_paid += final_amount
        fy.total_committed = max(Decimal("0"), fy.total_committed - payment.amount)
        fy.save(update_fields=["total_paid","total_committed","updated_at"])

        # Écriture de règlement
        self._create_entry(
            payment=payment,
            entry_type=FinancialEntry.EntryType.CREDIT,
            label=f"Règlement {payment.reference} — Réf: {bank_reference}",
            amount=final_amount, user=user,
        )
        audit.log_action(
            action="PAY", user=user, obj=payment, request=request,
            extra_data={"bank_reference": bank_reference, "amount": str(final_amount)},
            severity="CRITICAL",
        )
        return payment

    @transaction.atomic
    def cancel(self, payment: Payment, reason: str, user=None, request=None) -> Payment:
        """Annulation d'un paiement (uniquement si non payé)."""
        if not payment.can_be_cancelled():
            raise FinanceValidationError(
                "Un paiement payé ne peut pas être annulé. Créez une écriture d'annulation.",
                "CANNOT_CANCEL_PAID",
            )
        if not reason.strip():
            raise FinanceValidationError("Le motif d'annulation est obligatoire.")

        old_status = payment.status
        payment.status = Payment.Status.CANCELLED
        if user:
            payment.updated_by = user
        suffix = f"[Annulé le {timezone.now():%Y-%m-%d} par {user}] {reason}"
        payment.notes = f"{payment.notes}\n{suffix}" if payment.notes else suffix
        payment.save(update_fields=["status","notes","updated_at","updated_by"])

        # Libérer la réservation
        if payment.budget:
            budget = payment.budget
            budget.reserved_amount = max(Decimal("0"), budget.reserved_amount - payment.amount)
            budget.save(update_fields=["reserved_amount","updated_at"])

        audit.log_action(
            action="UPDATE", user=user, obj=payment, request=request,
            before_data={"status": old_status}, after_data={"status": "cancelled"},
            extra_data={"reason": reason}, severity="HIGH",
        )
        return payment

    def _create_entry(self, payment: Payment, entry_type: str,
                      label: str, amount: Decimal, user=None):
        """Crée une écriture comptable liée au paiement."""
        try:
            FinancialEntry.objects.create(
                fiscal_year=payment.fiscal_year,
                payment=payment,
                budget=payment.budget,
                entry_type=entry_type,
                label=label,
                amount=amount,
                entry_date=timezone.now().date(),
                accounting_date=timezone.now().date(),
                created_by_user=user,
            )
        except Exception as e:
            logger.error(f"Accounting entry failed for {payment.reference}: {e}", exc_info=True)

    def _check_and_create_alerts(self, payment: Payment):
        try:
            threshold = getattr(settings, "FINANCE_LARGE_PAYMENT_THRESHOLD", 500000)
            if payment.amount > Decimal(threshold):
                FinancialAlert.objects.create(
                    alert_type=FinancialAlert.AlertType.LARGE_PAYMENT,
                    severity=FinancialAlert.Severity.WARNING,
                    title=f"Paiement élevé — {payment.reference}",
                    message=(
                        f"Paiement de {payment.amount:,.0f} DZD pour "
                        f"{payment.employee.get_full_name()} — {payment.benefit.benefit_type.name}. "
                        f"Vérification recommandée."
                    ),
                    payment=payment,
                    fiscal_year=payment.fiscal_year,
                )
            # Alerte budget
            if payment.budget and payment.budget.is_alert_triggered:
                existing = FinancialAlert.objects.filter(
                    alert_type=FinancialAlert.AlertType.BUDGET_THRESHOLD,
                    budget=payment.budget,
                    is_resolved=False,
                ).exists()
                if not existing:
                    FinancialAlert.objects.create(
                        alert_type=FinancialAlert.AlertType.BUDGET_THRESHOLD,
                        severity=FinancialAlert.Severity.WARNING,
                        title=f"Seuil budgétaire atteint — {payment.budget.code}",
                        message=(
                            f"Le budget {payment.budget.label} a atteint "
                            f"{payment.budget.consumption_rate:.1f}% de consommation "
                            f"(seuil: {payment.budget.alert_threshold_pct}%)."
                        ),
                        budget=payment.budget,
                        fiscal_year=payment.fiscal_year,
                    )
        except Exception as e:
            logger.warning(f"Alert creation failed: {e}")


class PaymentBatchService:
    """Gestion des lots de paiements."""

    @transaction.atomic
    def create(self, data: dict, payment_ids: list, user=None, request=None) -> PaymentBatch:
        payments = Payment.objects.filter(
            id__in=payment_ids, status=Payment.Status.APPROVED, is_deleted=False
        )
        if not payments.exists():
            raise FinanceValidationError("Aucun paiement approuvé sélectionné.")
        batch = PaymentBatch(**data)
        batch.status = PaymentBatch.Status.SUBMITTED
        if user:
            batch.created_by = user
            batch.submitted_by = user
        batch.save()
        payments.update(batch=batch)
        batch.recalculate()
        audit.log_create(user=user, obj=batch, request=request)
        return batch

    @transaction.atomic
    def approve(self, batch: PaymentBatch, user=None) -> PaymentBatch:
        if batch.status != PaymentBatch.Status.SUBMITTED:
            raise FinanceValidationError("Seul un lot soumis peut être approuvé.")
        batch.status      = PaymentBatch.Status.APPROVED
        batch.approved_by = user
        batch.approved_at = timezone.now()
        batch.save(update_fields=["status","approved_by","approved_at","updated_at"])
        batch.payments.filter(is_deleted=False).update(status=Payment.Status.PROCESSING)
        audit.log_action(action="APPROVE", user=user, obj=batch, severity="CRITICAL")
        return batch


class FinancialReportService:
    """Service de reporting financier — source pour dashboard et exports."""

    def get_dashboard_summary(self, fiscal_year_id: str = None) -> dict:
        """Résumé complet pour le dashboard finance."""
        if not fiscal_year_id:
            fy = FiscalYearService().get_active_year()
        else:
            fy = FiscalYear.objects.filter(id=fiscal_year_id).first()
        if not fy:
            return {}

        pay_qs = Payment.objects.filter(fiscal_year=fy, is_deleted=False)
        bud_qs = Budget.objects.filter(fiscal_year=fy, is_deleted=False)

        by_status = {
            row["status"]: row
            for row in pay_qs.values("status").annotate(
                count=Count("id"), total=Sum("amount")
            )
        }

        # Tendance mensuelle
        from django.db.models.functions import TruncMonth
        monthly = list(
            pay_qs.filter(status=Payment.Status.PAID, executed_date__isnull=False)
            .annotate(month=TruncMonth("executed_date"))
            .values("month")
            .annotate(count=Count("id"), amount=Sum("amount"))
            .order_by("month")
        )

        # Top dépenses par type de prestation
        top_types = list(
            pay_qs.filter(status=Payment.Status.PAID)
            .values("benefit__benefit_type__code", "benefit__benefit_type__name")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")[:8]
        )

        # Alertes non résolues
        alerts = list(
            FinancialAlert.objects.filter(
                fiscal_year=fy, is_resolved=False
            ).values("alert_type", "severity", "title", "created_at").order_by("-created_at")[:10]
        )

        return {
            "fiscal_year": {
                "id": str(fy.id), "year": fy.year, "label": fy.label,
                "status": fy.status, "consumption_rate": float(fy.consumption_rate),
                "total_budget": float(fy.total_budget), "total_paid": float(fy.total_paid),
                "total_committed": float(fy.total_committed), "available": float(fy.available_budget),
            },
            "payments": {
                "total_count":   pay_qs.count(),
                "paid_count":    by_status.get("paid",    {}).get("count",  0),
                "pending_count": (by_status.get("pending",{}).get("count",  0) +
                                  by_status.get("approved",{}).get("count", 0)),
                "total_paid":    float(by_status.get("paid",{}).get("total", 0) or 0),
                "anomaly_count": pay_qs.filter(anomaly_flag=True).count(),
                "by_status":     [
                    {"status": s, "count": d["count"], "total": float(d["total"] or 0)}
                    for s, d in by_status.items()
                ],
            },
            "budgets": {
                "total_count":   bud_qs.count(),
                "overrun_count": sum(1 for b in bud_qs if b.is_overrun),
                "alert_count":   sum(1 for b in bud_qs if b.is_alert_triggered),
                "total_allocated": float(bud_qs.aggregate(s=Sum("allocated_amount"))["s"] or 0),
                "total_paid":      float(bud_qs.aggregate(s=Sum("paid_amount"))["s"] or 0),
            },
            "monthly_trend": [
                {"month": str(m["month"])[:7], "count": m["count"], "amount": float(m["amount"] or 0)}
                for m in monthly
            ],
            "top_benefit_types": [
                {"code": t["benefit__benefit_type__code"], "name": t["benefit__benefit_type__name"],
                 "count": t["count"], "total": float(t["total"] or 0)}
                for t in top_types
            ],
            "alerts": alerts,
        }

    def get_payment_export_data(self, filters: dict) -> list:
        """Données pour l'export Excel des paiements."""
        svc = PaymentService()
        qs  = svc.search(svc.get_queryset(), **filters)
        return [
            {
                "Référence":           p.reference,
                "Employé":             p.employee.get_full_name(),
                "Matricule":           p.employee.matricule,
                "Département":         p.employee.department.name if p.employee.department else "",
                "Prestation":          p.benefit.benefit_type.name,
                "Type prestation":     p.benefit.benefit_type.category,
                "Montant (DZD)":       float(p.amount),
                "Frais (DZD)":         float(p.fees),
                "Montant net (DZD)":   float(p.net_amount),
                "Statut":              p.get_status_display(),
                "Mode de paiement":    p.get_payment_method_display(),
                "Réf. bancaire":       p.bank_reference,
                "Date d'exécution":    p.executed_date.strftime("%d/%m/%Y") if p.executed_date else "",
                "Budget":              p.budget.code if p.budget else "",
                "Exercice":            p.fiscal_year.year,
                "Anomalie IA":         "Oui" if p.anomaly_flag else "Non",
            }
            for p in qs.iterator()
        ]

    def get_budget_export_data(self, fiscal_year_id: str) -> list:
        """Données pour l'export Excel des budgets."""
        budgets = Budget.objects.filter(
            fiscal_year_id=fiscal_year_id, is_deleted=False
        ).select_related("benefit_type","department","fiscal_year")
        return [
            {
                "Code":                b.code,
                "Libellé":             b.label,
                "Type prestation":     b.benefit_type.name if b.benefit_type else "",
                "Département":         b.department.name   if b.department   else "",
                "Statut":              b.get_status_display(),
                "Alloué (DZD)":        float(b.allocated_amount),
                "Payé (DZD)":          float(b.paid_amount),
                "Engagé (DZD)":        float(b.committed_amount),
                "Réservé (DZD)":       float(b.reserved_amount),
                "Disponible (DZD)":    float(b.available_amount),
                "Consommation (%)":    float(b.consumption_rate),
                "Alerte":              "Oui" if b.is_alert_triggered else "Non",
                "Dépassement":         "Oui" if b.is_overrun else "Non",
            }
            for b in budgets
        ]
