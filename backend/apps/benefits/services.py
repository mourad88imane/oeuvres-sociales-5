"""
============================================================
BENEFITS SERVICE — Logique métier prestations
============================================================
Toute la logique passe par ce service.
Les vues ne font que HTTP → Service → Réponse.
"""

import logging

from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from shared.audit.services import AuditService
from shared.workflow.engine import WorkflowEngine, WorkflowError

from .models import Benefit, BenefitAttachment, BenefitComment
from .workflow import benefit_workflow

logger = logging.getLogger("apps.benefits")
audit = AuditService()
engine = WorkflowEngine(benefit_workflow)


class BenefitService:

    # ── Requêtes ─────────────────────────────────────────
    def get_queryset(self):
        return Benefit.objects.select_related(
            "employee",
            "employee__department",
            "benefit_type",
            "beneficiary",
            "validated_by",
            "paid_by",
            "created_by",
            "last_transition_by",
        ).prefetch_related("attachments", "comments")

    def search(
        self,
        queryset,
        search_term: str = "",
        workflow_state: str = "",
        benefit_type_id: str = "",
        employee_id: str = "",
        department_id: str = "",
        priority: str = "",
        is_overdue: bool | None = None,
        ai_anomaly: bool | None = None,
        date_from: str = "",
        date_to: str = "",
        ordering: str = "-created_at",
    ):
        if search_term:
            queryset = queryset.filter(
                Q(reference__icontains=search_term)
                | Q(title__icontains=search_term)
                | Q(employee__first_name__icontains=search_term)
                | Q(employee__last_name__icontains=search_term)
                | Q(employee__matricule__icontains=search_term)
            )
        if workflow_state:
            queryset = queryset.filter(workflow_state=workflow_state)
        if benefit_type_id:
            queryset = queryset.filter(benefit_type_id=benefit_type_id)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if priority:
            queryset = queryset.filter(priority=priority)
        if ai_anomaly is not None:
            queryset = queryset.filter(ai_anomaly_flag=ai_anomaly)
        if date_from:
            queryset = queryset.filter(submitted_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(submitted_at__date__lte=date_to)
        if is_overdue:
            from datetime import date

            queryset = queryset.filter(due_date__lt=date.today()).exclude(
                workflow_state__in=["paid", "rejected", "cancelled"]
            )

        allowed_orderings = {
            "-created_at",
            "created_at",
            "-submitted_at",
            "submitted_at",
            "-requested_amount",
            "requested_amount",
            "priority",
            "-workflow_state",
            "workflow_state",
            "reference",
            "-reference",
        }
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        return queryset

    # ── CRUD ─────────────────────────────────────────────
    @transaction.atomic
    def create(self, validated_data: dict, user=None, request=None) -> Benefit:
        benefit = Benefit(**validated_data)
        benefit.workflow_state = "draft"
        if user:
            benefit.created_by = user
            benefit.updated_by = user
        benefit.save()
        audit.log_create(user=user, obj=benefit, request=request)
        logger.info("Benefit created", extra={"ref": benefit.reference, "by": str(user)})
        return benefit

    @transaction.atomic
    def update(self, benefit: Benefit, validated_data: dict, user=None, request=None) -> Benefit:
        # Seul un brouillon peut être modifié librement
        if benefit.workflow_state not in ("draft", "on_hold"):
            raise WorkflowError(
                "Seules les demandes en brouillon ou en attente peuvent être modifiées.",
                "EDIT_FORBIDDEN",
            )
        from django.forms.models import model_to_dict

        before = model_to_dict(benefit, exclude=["attachments", "comments"])
        for attr, value in validated_data.items():
            setattr(benefit, attr, value)
        if user:
            benefit.updated_by = user
        benefit.save()
        audit.log_update(user=user, obj=benefit, before_data=before, request=request)
        return benefit

    @transaction.atomic
    def delete(self, benefit: Benefit, user=None, request=None):
        if benefit.workflow_state not in ("draft", "cancelled", "rejected"):
            raise WorkflowError(
                "Seules les demandes en brouillon, annulées ou rejetées peuvent être supprimées.",
                "DELETE_FORBIDDEN",
            )
        audit.log_delete(user=user, obj=benefit, request=request)
        benefit.soft_delete(user=user)

    # ── Transitions workflow ──────────────────────────────
    @transaction.atomic
    def transition(
        self,
        benefit: Benefit,
        to_state: str,
        user=None,
        reason: str = "",
        metadata: dict = None,
        request=None,
    ):
        """
        Exécute une transition de workflow.
        Point central — toutes les transitions passent ici.
        """
        result = engine.transition(
            instance=benefit,
            to_state=to_state,
            actor=user,
            reason=reason,
            metadata=metadata or {},
            request=request,
        )
        # Mise à jour des champs de dernière transition
        benefit.last_transition_at = timezone.now()
        benefit.last_transition_by = user
        benefit.last_transition_reason = reason
        benefit.save(
            update_fields=["last_transition_at", "last_transition_by", "last_transition_reason"]
        )

        audit.log_workflow_transition(
            user=user,
            obj=benefit,
            from_state=result.from_state,
            to_state=result.to_state,
            request=request,
        )
        return result

    def get_available_transitions(self, benefit: Benefit, user) -> list:
        """
        Retourne les transitions disponibles pour cet utilisateur
        AVEC leur statut can/cannot (pour l'UI).
        """
        role = getattr(user, "role", "")
        defn = benefit_workflow
        results = []
        for transition in defn.get_available_transitions(benefit.workflow_state, role):
            can, reason = engine.can_transition(benefit, transition.to_state, actor=user)
            state_meta = defn.STATES.get(transition.to_state, {})
            results.append(
                {
                    "to_state": transition.to_state,
                    "label": transition.name,
                    "state_label": state_meta.get("label", transition.to_state),
                    "can_execute": can,
                    "blocked_reason": reason if not can else "",
                    "requires_reason": transition.requires_reason,
                    "severity": transition.severity,
                }
            )
        return results

    # ── Pièces jointes ────────────────────────────────────
    @transaction.atomic
    def add_attachment(
        self, benefit: Benefit, file, doc_type: str, description: str, user=None
    ) -> BenefitAttachment:
        att = BenefitAttachment(
            benefit=benefit,
            file=file,
            original_name=file.name,
            doc_type=doc_type,
            description=description,
            mime_type=getattr(file, "content_type", ""),
            uploaded_by=user,
        )
        if user:
            att.created_by = user
        att.save()
        audit.log_action(
            action="CREATE",
            user=user,
            obj=att,
            extra_data={"benefit_ref": benefit.reference},
        )
        return att

    def delete_attachment(self, att: BenefitAttachment, user=None):
        att.file.delete(save=False)
        att.soft_delete(user=user)

    # ── Commentaires ──────────────────────────────────────
    @transaction.atomic
    def add_comment(
        self,
        benefit: Benefit,
        content: str,
        comment_type: str = "internal",
        user=None,
    ) -> BenefitComment:
        comment = BenefitComment(
            benefit=benefit,
            author=user,
            content=content,
            comment_type=comment_type,
            workflow_state_at_time=benefit.workflow_state,
        )
        if user:
            comment.created_by = user
        comment.save()
        return comment

    # ── Statistiques / Dashboard ──────────────────────────
    def get_statistics(self, filters: dict = None) -> dict:
        """
        Statistiques complètes pour le dashboard et les analytics AI.
        Peut être filtré par département, période, type, etc.
        """

        qs = Benefit.objects.filter(is_deleted=False)
        if filters:
            if filters.get("department_id"):
                qs = qs.filter(employee__department_id=filters["department_id"])
            if filters.get("benefit_type_id"):
                qs = qs.filter(benefit_type_id=filters["benefit_type_id"])
            if filters.get("year"):
                qs = qs.filter(created_at__year=filters["year"])

        by_state = {
            row["workflow_state"]: row["count"]
            for row in qs.values("workflow_state").annotate(count=Count("id"))
        }

        paid_qs = qs.filter(workflow_state="paid")
        pending_qs = qs.filter(workflow_state__in=["submitted", "under_review", "on_hold"])

        stats = {
            "total": qs.count(),
            "by_state": by_state,
            "pending_count": pending_qs.count(),
            "paid_count": paid_qs.count(),
            "rejected_count": qs.filter(workflow_state="rejected").count(),
            "anomaly_count": qs.filter(ai_anomaly_flag=True).count(),
            # Montants
            "total_requested": float(qs.aggregate(s=Sum("requested_amount"))["s"] or 0),
            "total_approved": float(
                qs.filter(approved_amount__isnull=False).aggregate(s=Sum("approved_amount"))["s"]
                or 0
            ),
            "total_paid": float(paid_qs.aggregate(s=Sum("paid_amount"))["s"] or 0),
            # Par type
            "by_type": list(
                qs.values("benefit_type__code", "benefit_type__name", "benefit_type__category")
                .annotate(count=Count("id"), total_amount=Sum("requested_amount"))
                .order_by("-count")
            ),
            # Par priorité
            "by_priority": list(qs.values("priority").annotate(count=Count("id"))),
            # Délai moyen de traitement (jours) — dataset AI
            "avg_processing_days": self._avg_processing_days(paid_qs),
            # Tendance mensuelle (12 derniers mois)
            "monthly_trend": self._monthly_trend(qs),
            # SLA : taux dans les délais
            "sla_rate": self._compute_sla_rate(paid_qs),
        }
        return stats

    def _avg_processing_days(self, qs) -> float | None:
        from django.db.models import ExpressionWrapper, FloatField, F
        from django.db.models.functions import Extract

        annotated = qs.filter(submitted_at__isnull=False, paid_at__isnull=False).annotate(
            days=ExpressionWrapper(
                Extract(F("paid_at") - F("submitted_at"), "epoch") / 86400,
                output_field=FloatField(),
            )
        )
        agg = annotated.aggregate(avg=Avg("days"))
        return round(agg["avg"], 1) if agg.get("avg") else None

    def _monthly_trend(self, qs) -> list:
        from django.db.models.functions import TruncMonth

        return list(
            qs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=365))
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"), amount=Sum("requested_amount"))
            .order_by("month")
        )

    def _compute_sla_rate(self, paid_qs) -> float | None:
        """Taux de dossiers traités dans le délai cible du type de prestation."""
        total = paid_qs.filter(benefit_type__target_processing_days__isnull=False).count()
        if not total:
            return None
        on_time = (
            paid_qs.filter(
                benefit_type__target_processing_days__isnull=False,
            )
            .extra(
                where=[
                    "EXTRACT(EPOCH FROM (paid_at - submitted_at)) / 86400 <= apps_benefits_benefittype.target_processing_days"
                ]
            )
            .count()
        )
        return round((on_time / total) * 100, 1)

    def get_employee_benefits_summary(self, employee_id: str) -> dict:
        """Résumé des prestations d'un employé (pour sa fiche)."""
        qs = Benefit.objects.filter(employee_id=employee_id, is_deleted=False)
        return {
            "total": qs.count(),
            "pending": qs.filter(
                workflow_state__in=["draft", "submitted", "under_review", "on_hold"]
            ).count(),
            "paid": qs.filter(workflow_state="paid").count(),
            "total_paid_amount": float(
                qs.filter(workflow_state="paid").aggregate(s=Sum("paid_amount"))["s"] or 0
            ),
            "by_type": list(
                qs.values("benefit_type__name", "benefit_type__category").annotate(
                    count=Count("id")
                )
            ),
        }
