import logging

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from shared.audit.services import AuditService
from shared.workflow.engine import WorkflowEngine, WorkflowError

from .models import Loan, LoanAttachment, LoanComment
from .workflow import loan_workflow

logger = logging.getLogger("apps.loans")
audit = AuditService()
engine = WorkflowEngine(loan_workflow)


class LoanService:

    def get_queryset(self):
        return Loan.objects.select_related(
            "employee",
            "employee__department",
            "validated_by",
            "paid_by",
            "created_by",
            "last_transition_by",
        ).prefetch_related("attachments", "comments")

    def search(self, queryset, search_term="", workflow_state="", employee_id="",
               department_id="", date_from="", date_to="", ordering="-created_at"):
        if search_term:
            queryset = queryset.filter(
                Q(reference__icontains=search_term)
                | Q(reason__icontains=search_term)
                | Q(employee__first_name__icontains=search_term)
                | Q(employee__last_name__icontains=search_term)
                | Q(employee__matricule__icontains=search_term)
            )
        if workflow_state:
            queryset = queryset.filter(workflow_state=workflow_state)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        if date_from:
            queryset = queryset.filter(submitted_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(submitted_at__date__lte=date_to)

        allowed_orderings = {
            "-created_at", "created_at", "-submitted_at", "submitted_at",
            "-requested_amount", "requested_amount", "reference", "-reference",
        }
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        return queryset

    @transaction.atomic
    def create(self, validated_data, user=None, request=None) -> Loan:
        loan = Loan(**validated_data)
        loan.workflow_state = "draft"
        if user:
            loan.created_by = user
            loan.updated_by = user
        loan.save()
        audit.log_create(user=user, obj=loan, request=request)
        logger.info("Loan created", extra={"ref": loan.reference, "by": str(user)})
        return loan

    @transaction.atomic
    def update(self, loan, validated_data, user=None, request=None) -> Loan:
        if loan.workflow_state not in ("draft", "on_hold"):
            raise WorkflowError(
                "Seules les demandes en brouillon ou en attente peuvent être modifiées.",
                "EDIT_FORBIDDEN",
            )
        from django.forms.models import model_to_dict
        before = model_to_dict(loan)
        for attr, value in validated_data.items():
            setattr(loan, attr, value)
        if user:
            loan.updated_by = user
        loan.save()
        audit.log_update(user=user, obj=loan, before_data=before, request=request)
        return loan

    @transaction.atomic
    def delete(self, loan, user=None, request=None):
        if loan.workflow_state not in ("draft", "cancelled", "rejected"):
            raise WorkflowError(
                "Seules les demandes en brouillon, annulées ou rejetées peuvent être supprimées.",
                "DELETE_FORBIDDEN",
            )
        audit.log_delete(user=user, obj=loan, request=request)
        loan.soft_delete(user=user)

    @transaction.atomic
    def transition(self, loan, to_state, user=None, reason="", metadata=None, request=None):
        result = engine.transition(
            instance=loan, to_state=to_state, actor=user,
            reason=reason, metadata=metadata or {}, request=request,
        )
        loan.last_transition_at = timezone.now()
        loan.last_transition_by = user
        loan.last_transition_reason = reason
        loan.save(update_fields=["last_transition_at", "last_transition_by", "last_transition_reason"])
        audit.log_workflow_transition(
            user=user, obj=loan, from_state=result.from_state,
            to_state=result.to_state, request=request,
        )
        return result

    def get_available_transitions(self, loan, user) -> list:
        role = getattr(user, "role", "")
        defn = loan_workflow
        results = []
        for transition in defn.get_available_transitions(loan.workflow_state, role):
            can, reason = engine.can_transition(loan, transition.to_state, actor=user)
            state_meta = defn.STATES.get(transition.to_state, {})
            results.append({
                "to_state": transition.to_state,
                "label": transition.name,
                "state_label": state_meta.get("label", transition.to_state),
                "can_execute": can,
                "blocked_reason": reason if not can else "",
                "requires_reason": transition.requires_reason,
                "severity": transition.severity,
            })
        return results

    @transaction.atomic
    def add_attachment(self, loan, file, doc_type, description="", user=None) -> LoanAttachment:
        att = LoanAttachment(
            loan=loan, file=file, original_name=file.name, doc_type=doc_type,
            description=description, mime_type=getattr(file, "content_type", ""),
            uploaded_by=user,
        )
        if user:
            att.created_by = user
        att.save()
        return att

    def delete_attachment(self, att, user=None):
        att.file.delete(save=False)
        att.soft_delete(user=user)

    @transaction.atomic
    def add_comment(self, loan, content, comment_type="internal", user=None) -> LoanComment:
        comment = LoanComment(
            loan=loan, author=user, content=content, comment_type=comment_type,
            workflow_state_at_time=loan.workflow_state,
        )
        if user:
            comment.created_by = user
        comment.save()
        return comment

    def get_statistics(self, filters=None) -> dict:
        qs = Loan.objects.filter(is_deleted=False)
        if filters:
            if filters.get("department_id"):
                qs = qs.filter(employee__department_id=filters["department_id"])
            if filters.get("year"):
                qs = qs.filter(created_at__year=filters["year"])

        by_state = {
            row["workflow_state"]: row["count"]
            for row in qs.values("workflow_state").annotate(count=Count("id"))
        }
        paid_qs = qs.filter(workflow_state="paid")
        pending_qs = qs.filter(workflow_state__in=["submitted", "under_review", "on_hold"])

        return {
            "total": qs.count(),
            "by_state": by_state,
            "pending_count": pending_qs.count(),
            "paid_count": paid_qs.count(),
            "rejected_count": qs.filter(workflow_state="rejected").count(),
            "total_requested": float(qs.aggregate(s=Sum("requested_amount"))["s"] or 0),
            "total_approved": float(
                qs.filter(approved_amount__isnull=False).aggregate(s=Sum("approved_amount"))["s"] or 0
            ),
            "total_paid": float(paid_qs.aggregate(s=Sum("paid_amount"))["s"] or 0),
            "monthly_trend": list(
                qs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=365))
                .extra(select={"month": "strftime('%%Y-%%m', created_at)"})
                .values("month")
                .annotate(count=Count("id"), amount=Sum("requested_amount"))
                .order_by("month")
            ) if not hasattr(qs, "using") else [],
        }
