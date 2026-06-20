from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings

from shared.audit.services import AuditService
from shared.workflow.engine import WorkflowEngine, WorkflowError
from apps.medical_coverage.models import (
    MedicalCoverageVoucher, MedicalCoverageType, MedicalProvider,
    MedicalCoverageRequest,
)
from apps.medical_coverage.eligibility import EligibilityEngine


class MedicalCoverageService:
    def __init__(self):
        self.Voucher = MedicalCoverageVoucher
        self.audit = AuditService()
        self.eligibility = EligibilityEngine(self.Voucher)

    def get_queryset(self):
        return self.Voucher.objects.select_related(
            "coverage_type", "employee__department",
            "provider", "created_by", "beneficiary",
        )

    def search(self, filters=None):
        qs = self.get_queryset()
        f = filters or {}
        if f.get("coverage_type"):
            qs = qs.filter(coverage_type__code=f["coverage_type"])
        if f.get("employee"):
            qs = qs.filter(employee_id=f["employee"])
        if f.get("status"):
            qs = qs.filter(workflow_state=f["status"])
        if f.get("beneficiary_type"):
            qs = qs.filter(beneficiary_type=f["beneficiary_type"])
        if f.get("date_from"):
            qs = qs.filter(request_date__gte=f["date_from"])
        if f.get("date_to"):
            qs = qs.filter(request_date__lte=f["date_to"])
        if f.get("search"):
            search = f["search"]
            qs = qs.filter(
                Q(reference__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__matricule__icontains=search)
            )
        ordering = f.get("ordering", "-created_at")
        return qs.order_by(ordering)

    def get_employee_info(self, employee_id):
        from apps.employees.models import Employee
        try:
            employee = Employee.objects.select_related(
                "department"
            ).get(id=employee_id)
        except Employee.DoesNotExist:
            return None
        return {
            "id": str(employee.id),
            "matricule": employee.matricule,
            "full_name": f"{employee.first_name} {employee.last_name}",
            "department": employee.department.name if employee.department else "",
            "position": employee.job_title or "",
            "status": employee.status,
        }

    def get_employee_coverage_summary(self, employee_id, coverage_type_code=None):
        vouchers = self.Voucher.objects.filter(
            employee_id=employee_id,
            workflow_state__in=["approved", "consumed"],
        )
        if coverage_type_code:
            vouchers = vouchers.filter(coverage_type__code=coverage_type_code)

        total = vouchers.count()
        last = vouchers.order_by("-request_date").first()

        three_months_ago = timezone.now().date() - relativedelta(months=3)
        last_3m = vouchers.filter(request_date__gte=three_months_ago).count()

        year_start = date(timezone.now().year, 1, 1)
        this_year = vouchers.filter(request_date__gte=year_start).count()

        return {
            "total_vouchers": total,
            "last_voucher_reference": last.reference if last else None,
            "last_voucher_date": str(last.request_date) if last else None,
            "last_voucher_type": last.coverage_type.name if last else None,
            "count_last_3_months": last_3m,
            "count_current_year": this_year,
        }

    def get_dependents_summary(self, employee_id, coverage_type_code=None):
        vouchers = self.Voucher.objects.filter(
            employee_id=employee_id,
            beneficiary__isnull=False,
            workflow_state__in=["approved", "consumed"],
        )
        if coverage_type_code:
            vouchers = vouchers.filter(coverage_type__code=coverage_type_code)

        vouchers = vouchers.select_related("beneficiary")
        deps = {}
        for v in vouchers:
            b = v.beneficiary
            if b.id not in deps:
                deps[b.id] = {
                    "id": str(b.id),
                    "full_name": f"{b.first_name} {b.last_name}",
                    "relationship": b.relationship,
                    "relationship_display": b.get_relationship_display() if hasattr(b, "get_relationship_display") else b.relationship,
                    "last_voucher_date": None,
                    "last_voucher_reference": None,
                    "count_last_3_months": 0,
                }
            dep = deps[b.id]
            if not dep["last_voucher_date"] or v.request_date.isoformat() > dep["last_voucher_date"]:
                dep["last_voucher_date"] = str(v.request_date)
                dep["last_voucher_reference"] = v.reference
            three_months_ago = timezone.now().date() - relativedelta(months=3)
            if v.request_date >= three_months_ago:
                dep["count_last_3_months"] += 1

        return list(deps.values())

    @transaction.atomic
    def create(self, data, user):
        request_date = data.get("request_date") or timezone.now().date()
        coverage_type = data["coverage_type"]

        if data.get("beneficiary_type") == "dependent" and data.get("beneficiary"):
            result = self.eligibility.check_dependent_eligibility(
                employee=data["employee"], dependent=data["beneficiary"],
                coverage_type=coverage_type, request_date=request_date,
            )
        else:
            result = self.eligibility.check_employee_eligibility(
                employee=data["employee"],
                coverage_type=coverage_type, request_date=request_date,
            )

        voucher = self.Voucher(
            coverage_type=coverage_type,
            employee=data["employee"],
            beneficiary_type=data.get("beneficiary_type", "employee"),
            beneficiary=data.get("beneficiary"),
            provider=data.get("provider"),
            request_date=request_date,
            expected_date=data.get("expected_date"),
            observations=data.get("observations", ""),
            amount=data.get("amount"),
            workflow_state="draft",
            next_eligible_date=result.next_eligible_date,
            created_by=user,
            updated_by=user,
        )
        voucher.save()

        self.audit.log_create(voucher, user, extra_data={
            "eligibility": {
                "is_eligible": result.is_eligible,
                "messages": result.messages,
            }
        })
        return voucher

    @transaction.atomic
    def update(self, voucher_id, data, user):
        voucher = self.Voucher.objects.select_related("coverage_type").get(id=voucher_id)
        if voucher.workflow_state not in ("draft",):
            raise WorkflowError(_("Impossible de modifier un bon qui n'est pas en état brouillon."))

        for field in ("observations", "expected_date", "provider", "beneficiary", "amount", "approved_amount"):
            if field in data:
                setattr(voucher, field, data[field])
        voucher.updated_by = user
        voucher.save()
        self.audit.log_update(voucher, user)
        return voucher

    @transaction.atomic
    def transition(self, voucher_id, to_state, user, reason=None):
        from apps.medical_coverage.workflow import MedicalCoverageWorkflow
        voucher = self.Voucher.objects.get(id=voucher_id)
        engine = WorkflowEngine(MedicalCoverageWorkflow())
        result = engine.transition(
            instance=voucher,
            to_state=to_state,
            actor=user,
            reason=reason or "",
        )
        voucher.refresh_from_db()
        self.audit.log_workflow_transition(
            user=user,
            obj=voucher,
            from_state=result.from_state,
            to_state=result.to_state,
        )
        return voucher

    def get_available_transitions(self, voucher_id, user):
        from apps.medical_coverage.workflow import MedicalCoverageWorkflow
        voucher = self.Voucher.objects.get(id=voucher_id)
        defn = MedicalCoverageWorkflow()
        engine = WorkflowEngine(defn)
        role = getattr(user, "role", "")
        results = []
        for transition in defn.get_available_transitions(voucher.workflow_state, role):
            can, reason = engine.can_transition(voucher, transition.to_state, actor=user)
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

    def get_workflow_log(self, voucher_id):
        from shared.workflow.models import WorkflowLog
        return WorkflowLog.objects.filter(
            object_id=voucher_id,
            content_type__model="medicalcoveragevoucher",
        ).order_by("-timestamp")

    def get_statistics(self, coverage_type_code=None):
        qs = self.Voucher.objects.all()
        if coverage_type_code:
            qs = qs.filter(coverage_type__code=coverage_type_code)

        total = qs.count()
        by_status = qs.values("workflow_state").annotate(count=Count("id"))
        rejected = qs.filter(workflow_state="rejected").count()
        consumed = qs.filter(workflow_state="consumed").count()
        approved = qs.filter(workflow_state="approved").count()

        by_type = qs.values(
            "coverage_type__code", "coverage_type__name",
        ).annotate(count=Count("id")).order_by("-count")

        most_used = by_type.first()

        by_month = qs.filter(
            request_date__year=timezone.now().year,
        ).extra(
            {"month": "extract('month' FROM request_date)"}
        ).values("month").annotate(
            count=Count("id")
        ).order_by("month")

        employee_stats = qs.values(
            "employee__first_name", "employee__last_name", "employee__matricule",
        ).annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        dependent_stats = qs.filter(
            beneficiary__isnull=False,
        ).values(
            "beneficiary__first_name", "beneficiary__last_name",
        ).annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        return {
            "total": total,
            "consumed": consumed,
            "approved": approved,
            "rejected": rejected,
            "by_status": {s["workflow_state"]: s["count"] for s in by_status},
            "by_type": list(by_type),
            "most_used_type": most_used,
            "monthly_stats": list(by_month),
            "top_employees": list(employee_stats),
            "top_dependents": list(dependent_stats),
        }


class MedicalCoverageRequestService:
    def __init__(self):
        self.Request = MedicalCoverageRequest
        self.audit = AuditService()

    def get_queryset(self):
        return self.Request.objects.select_related(
            "employee", "partner", "beneficiary", "created_by",
        )

    def search(self, params=None):
        qs = self.get_queryset()
        p = params or {}
        if p.get("category"):
            qs = qs.filter(category=p["category"])
        if p.get("employee"):
            qs = qs.filter(employee_id=p["employee"])
        if p.get("status"):
            qs = qs.filter(workflow_state=p["status"])
        if p.get("partner"):
            qs = qs.filter(partner_id=p["partner"])
        if p.get("date_from"):
            qs = qs.filter(coverage_date__gte=p["date_from"])
        if p.get("date_to"):
            qs = qs.filter(coverage_date__lte=p["date_to"])
        if p.get("search"):
            s = p["search"]
            qs = qs.filter(
                Q(request_number__icontains=s) |
                Q(employee__first_name__icontains=s) |
                Q(employee__last_name__icontains=s) |
                Q(employee__matricule__icontains=s)
            )
        ordering = p.get("ordering", "-created_at")
        return qs.order_by(ordering)

    def get_restriction_period_months(self) -> int:
        try:
            from apps.administration.models import SystemParameter
            param = SystemParameter.objects.get(key="coverage_restriction_period_months")
            return int(param.value)
        except (SystemParameter.DoesNotExist, ValueError, TypeError):
            return 3

    def count_requests_last_n_months(self, employee, beneficiary=None, months=None):
        if months is None:
            months = self.get_restriction_period_months()
        cutoff = timezone.now().date() - relativedelta(months=months)
        qs = self.Request.objects.filter(
            employee=employee,
            created_at__gte=cutoff,
        )
        if beneficiary:
            qs = qs.filter(beneficiary=beneficiary)
        else:
            qs = qs.filter(beneficiary__isnull=True)
        return qs.count()

    @transaction.atomic
    def create(self, data, user):
        coverage_date = data.get("coverage_date") or timezone.now().date()
        employee = data["employee"]
        beneficiary = data.get("beneficiary")
        restriction_months = self.get_restriction_period_months()
        req_count = self.count_requests_last_n_months(employee, beneficiary, months=restriction_months)

        if req_count == 0:
            workflow_state = "validated"
            validation_date = coverage_date
            approval_action = "auto_validated"
        else:
            workflow_state = "pending_manager_approval"
            validation_date = None
            approval_action = "pending_manager"

        request_obj = self.Request(
            category=data["category"],
            partner=data["partner"],
            employee=employee,
            beneficiary=beneficiary,
            coverage_date=coverage_date,
            validation_date=validation_date,
            observation=data.get("observation", ""),
            workflow_state=workflow_state,
            created_by=user,
            updated_by=user,
        )
        request_obj.save()

        from apps.administration.models import ApprovalHistory
        from django.contrib.contenttypes.models import ContentType
        ApprovalHistory.objects.create(
            content_type=ContentType.objects.get_for_model(request_obj),
            object_id=request_obj.pk,
            action=approval_action,
            user=user,
            comment=f"Période de restriction: {restriction_months} mois, demandes trouvées: {req_count}",
            from_state="draft",
            to_state=workflow_state,
        )

        self.audit.log_create(request_obj, user, extra_data={
            "auto_validated": req_count == 0,
            "requests_last_n_months": req_count,
            "restriction_period_months": restriction_months,
            "workflow_state": workflow_state,
        })

        return request_obj

    @transaction.atomic
    def transition(self, request_id, to_state, user, reason=None):
        from apps.medical_coverage.workflow import MedicalCoverageRequestWorkflow
        from apps.administration.models import ApprovalHistory
        from django.contrib.contenttypes.models import ContentType
        request_obj = self.Request.objects.get(id=request_id)
        engine = WorkflowEngine(MedicalCoverageRequestWorkflow())
        result = engine.transition(
            instance=request_obj,
            to_state=to_state,
            actor=user,
            reason=reason or "",
        )
        request_obj.refresh_from_db()

        if to_state == "validated" and not request_obj.validation_date:
            request_obj.validation_date = timezone.now().date()
            request_obj.save(update_fields=["validation_date", "updated_at"])

        action_map = {
            "validated": "approved",
            "rejected": "rejected",
            "pending_manager_approval": "pending_manager",
            "pending_director_approval": "escalated",
        }
        approval_action = action_map.get(to_state, to_state)
        ApprovalHistory.objects.create(
            content_type=ContentType.objects.get_for_model(request_obj),
            object_id=request_obj.pk,
            action=approval_action,
            user=user,
            comment=reason or "",
            from_state=result.from_state,
            to_state=to_state,
        )

        self.audit.log_workflow_transition(
            user=user,
            obj=request_obj,
            from_state=result.from_state,
            to_state=result.to_state,
        )
        return request_obj

    def get_available_transitions(self, request_id, user):
        from apps.medical_coverage.workflow import MedicalCoverageRequestWorkflow
        request_obj = self.Request.objects.get(id=request_id)
        defn = MedicalCoverageRequestWorkflow()
        engine = WorkflowEngine(defn)
        role = getattr(user, "role", "")
        results = []
        for transition in defn.get_available_transitions(request_obj.workflow_state, role):
            can, reason = engine.can_transition(request_obj, transition.to_state, actor=user)
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

    def get_statistics(self, category=None):
        qs = self.Request.objects.all()
        if category:
            qs = qs.filter(category=category)
        total = qs.count()
        pending = qs.filter(workflow_state__in=["draft", "submitted", "pending_approval", "pending_manager_approval", "pending_director_approval"]).count()
        validated = qs.filter(workflow_state="validated").count()
        printed = qs.filter(workflow_state="printed").count()
        by_partner = qs.values(
            "partner__name", "partner__id",
        ).annotate(count=Count("id")).order_by("-count")[:10]
        by_month = qs.extra(
            {"month": "extract('month' FROM coverage_date)"}
        ).values("month").annotate(count=Count("id")).order_by("month")
        return {
            "total": total,
            "pending": pending,
            "validated": validated,
            "printed": printed,
            "by_partner": list(by_partner),
            "by_month": list(by_month),
        }
