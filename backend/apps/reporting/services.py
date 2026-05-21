import hashlib
import json
import logging
from datetime import timedelta

from django.apps import apps
from django.core.cache import cache
from django.db import models
from django.utils import timezone

logger = logging.getLogger("apps.reporting")

_CACHE_TTL = 60 * 5  # 5 minutes

MONTHS_FR = [
    "Jan",
    "Fév",
    "Mar",
    "Avr",
    "Mai",
    "Juin",
    "Juil",
    "Août",
    "Sep",
    "Oct",
    "Nov",
    "Déc",
]


class AggregationService:

    def _cache_key(self, prefix, **params):
        raw = json.dumps(params, sort_keys=True, default=str)
        h = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"agg:{prefix}:{h}"

    def _cached(self, key, func, ttl=_CACHE_TTL):
        data = cache.get(key)
        if data is not None:
            return data
        data = func()
        cache.set(key, data, ttl)
        return data

    def get_global_stats(self, user=None):
        key = self._cache_key("global_stats", user=str(getattr(user, "pk", "")))
        return self._cached(key, lambda: self._compute_global_stats())

    def _compute_global_stats(self):
        Employee = apps.get_model("employees", "Employee")
        Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
        Benefit = apps.get_model("benefits", "Benefit")
        Convention = apps.get_model("conventions", "Convention")
        Budget = apps.get_model("finance", "Budget")
        Payment = apps.get_model("finance", "Payment")

        today = timezone.localdate()
        month_start = today.replace(day=1)
        today.replace(month=1, day=1)

        return {
            "employees": {
                "total": Employee.objects.alive().count(),
                "active": Employee.objects.alive().filter(status="active").count(),
                "new_this_month": Employee.objects.alive()
                .filter(created_at__date__gte=month_start)
                .count(),
                "by_department": list(
                    Employee.objects.alive()
                    .values("department__name")
                    .annotate(count=models.Count("id"))
                    .order_by("-count")
                ),
                "by_wilaya": list(
                    Employee.objects.alive()
                    .values("wilaya")
                    .annotate(count=models.Count("id"))
                    .order_by("-count")[:10]
                ),
            },
            "beneficiaries": {
                "total": Beneficiary.objects.alive().count(),
                "active": Beneficiary.objects.alive().filter(is_eligible=True).count(),
                "new_this_month": Beneficiary.objects.alive()
                .filter(created_at__date__gte=month_start)
                .count(),
            },
            "benefits": {
                "total": Benefit.objects.alive().count(),
                "pending": Benefit.objects.alive().filter(workflow_state__in=["submitted", "under_review", "on_hold"]).count(),
                "approved": Benefit.objects.alive().filter(workflow_state="validated").count(),
                "paid": Benefit.objects.alive().filter(workflow_state="paid").count(),
                "rejected": Benefit.objects.alive().filter(workflow_state="rejected").count(),
                "total_amount": Benefit.objects.alive().aggregate(total=models.Sum("requested_amount"))[
                    "total"
                ]
                or 0,
                "month_amount": Benefit.objects.alive()
                .filter(created_at__date__gte=month_start)
                .aggregate(total=models.Sum("requested_amount"))["total"]
                or 0,
                "by_type": list(
                    Benefit.objects.alive()
                    .values("benefit_type__name")
                    .annotate(
                        count=models.Count("id"),
                        total=models.Sum("requested_amount"),
                    )
                    .order_by("-count")
                ),
            },
            "conventions": {
                "total": Convention.objects.alive().count(),
                "active": Convention.objects.alive().filter(status="active").count(),
                "expiring_soon": Convention.objects.alive()
                .filter(
                    end_date__lte=today + timedelta(days=30),
                    end_date__gte=today,
                )
                .count(),
                "expired": Convention.objects.alive()
                .filter(end_date__lt=today, status__in=["active", "expiring_soon"])
                .count(),
            },
            "finance": {
                "total_budget": Budget.objects.alive().aggregate(
                    total=models.Sum("allocated_amount")
                )["total"]
                or 0,
                "total_paid": Payment.objects.alive()
                .filter(status="paid")
                .aggregate(total=models.Sum("amount"))["total"]
                or 0,
                "pending_payments": Payment.objects.alive()
                .filter(status__in=["pending", "approved"])
                .count(),
                "month_paid": Payment.objects.alive()
                .filter(status="paid", executed_date__gte=month_start)
                .aggregate(total=models.Sum("amount"))["total"]
                or 0,
            },
        }

    def get_monthly_trends(self, months=12):
        key = self._cache_key("monthly_trends", months=months)
        return self._cached(key, lambda: self._compute_monthly_trends(months))

    def _compute_monthly_trends(self, months=12):
        today = timezone.localdate()
        today - timedelta(days=months * 30)
        Benefit = apps.get_model("benefits", "Benefit")
        Payment = apps.get_model("finance", "Payment")
        Convention = apps.get_model("conventions", "Convention")

        months_data = []
        for i in range(months - 1, -1, -1):
            m_start = (today - timedelta(days=30 * i)).replace(day=1)
            if i > 0:
                m_end = (today - timedelta(days=30 * (i - 1))).replace(day=1) - timedelta(days=1)
            else:
                m_end = today
            label = f"{MONTHS_FR[m_start.month - 1]} {m_start.year}"
            months_data.append(
                {
                    "month": label,
                    "date": m_start.isoformat(),
                    "benefits_count": Benefit.objects.alive()
                    .filter(created_at__date__gte=m_start, created_at__date__lte=m_end)
                    .count(),
                    "benefits_amount": Benefit.objects.alive()
                    .filter(created_at__date__gte=m_start, created_at__date__lte=m_end)
                    .aggregate(total=models.Sum("requested_amount"))["total"]
                    or 0,
                    "payments_count": Payment.objects.alive()
                    .filter(executed_date__gte=m_start, executed_date__lte=m_end)
                    .count(),
                    "payments_amount": Payment.objects.alive()
                    .filter(executed_date__gte=m_start, executed_date__lte=m_end)
                    .aggregate(total=models.Sum("amount"))["total"]
                    or 0,
                    "conventions_created": Convention.objects.alive()
                    .filter(created_at__date__gte=m_start, created_at__date__lte=m_end)
                    .count(),
                }
            )

        return months_data

    def get_top_stats(self, limit=10):
        key = self._cache_key("top_stats", limit=limit)
        return self._cached(key, lambda: self._compute_top_stats(limit))

    def _compute_top_stats(self, limit=10):
        Benefit = apps.get_model("benefits", "Benefit")
        apps.get_model("employees", "Employee")
        apps.get_model("finance", "Payment")

        return {
            "top_benefit_types": list(
                Benefit.objects.alive()
                .values("benefit_type__name", "benefit_type__code")
                .annotate(
                    count=models.Count("id"),
                    total=models.Sum("requested_amount"),
                )
                .order_by("-total")[:limit]
            ),
            "top_departments_by_benefits": list(
                Benefit.objects.alive()
                .values("employee__department__name")
                .annotate(
                    count=models.Count("id"),
                    total=models.Sum("requested_amount"),
                )
                .order_by("-total")[:limit]
            ),
            "top_employees_by_amount": list(
                Benefit.objects.alive()
                .values("employee__matricule")
                .annotate(
                    full_name=models.functions.Concat(
                        models.F("employee__first_name"),
                        models.Value(" "),
                        models.F("employee__last_name"),
                    ),
                    count=models.Count("id"),
                    total=models.Sum("requested_amount"),
                )
                .order_by("-total")[:limit]
            ),
            "top_partners": list(
                apps.get_model("conventions", "Convention")
                .objects.alive()
                .values("partner__name", "partner__code")
                .annotate(
                    count=models.Count("id"),
                    total=models.Sum("amount"),
                )
                .order_by("-total")[:limit]
            ),
        }

    def get_all_kpis(self):
        key = self._cache_key("all_kpis")
        return self._cached(key, lambda: self._compute_all_kpis(), ttl=60 * 2)

    def _compute_all_kpis(self):
        KpiDefinition = apps.get_model("reporting", "KpiDefinition")
        kpis = KpiDefinition.objects.filter(is_active=True)
        results = []
        for kpi in kpis:
            latest = kpi.snapshots.order_by("-date").first()
            results.append(
                {
                    "id": str(kpi.id),
                    "code": kpi.code,
                    "name": kpi.name,
                    "description": kpi.description,
                    "category": kpi.category,
                    "unit": kpi.unit,
                    "target_value": kpi.target_value,
                    "current_value": latest.value if latest else None,
                    "previous_value": latest.previous_value if latest else None,
                    "variation": latest.variation if latest else None,
                    "date": latest.date.isoformat() if latest else None,
                    "trend": self._compute_trend(latest.variation) if latest else "stable",
                }
            )
        return results

    def _compute_trend(self, variation):
        if variation is None:
            return "stable"
        if variation > 5:
            return "up"
        if variation < -5:
            return "down"
        return "stable"

    def compute_and_snapshot_kpis(self):
        KpiDefinition = apps.get_model("reporting", "KpiDefinition")
        KpiSnapshot = apps.get_model("reporting", "KpiSnapshot")
        today = timezone.localdate()
        results = []

        computed = self._compute_all_kpi_values()
        for code, value in computed.items():
            kpi = KpiDefinition.objects.filter(code=code).first()
            if not kpi:
                continue
            previous = KpiSnapshot.objects.filter(kpi=kpi).order_by("-date").first()
            prev_val = previous.value if previous else None
            variation = None
            if prev_val and prev_val != 0:
                variation = round(((value - prev_val) / prev_val) * 100, 2)

            KpiSnapshot.objects.update_or_create(
                kpi=kpi,
                date=today,
                defaults={
                    "value": value,
                    "previous_value": prev_val,
                    "variation": variation,
                },
            )
            results.append({"code": code, "value": value, "variation": variation})

        return results

    def _compute_all_kpi_values(self):
        Employee = apps.get_model("employees", "Employee")
        Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
        Benefit = apps.get_model("benefits", "Benefit")
        Convention = apps.get_model("conventions", "Convention")
        Budget = apps.get_model("finance", "Budget")
        Payment = apps.get_model("finance", "Payment")
        today = timezone.localdate()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        total_employees = Employee.objects.alive().count()
        active_employees = Employee.objects.alive().filter(status="active").count()
        total_beneficiaries = Beneficiary.objects.alive().count()
        total_benefits = Benefit.objects.alive().count()
        total_benefits_amount = (
            Benefit.objects.alive().aggregate(total=models.Sum("requested_amount"))["total"] or 0
        )
        month_benefits_amount = (
            Benefit.objects.alive()
            .filter(created_at__date__gte=month_start)
            .aggregate(total=models.Sum("requested_amount"))["total"]
            or 0
        )
        total_conventions = Convention.objects.alive().count()
        active_conventions = Convention.objects.alive().filter(status="active").count()
        expired_conventions = (
            Convention.objects.alive()
            .filter(end_date__lt=today, status__in=["active", "expiring_soon"])
            .count()
        )
        total_budget = (
            Budget.objects.alive().aggregate(total=models.Sum("allocated_amount"))["total"] or 0
        )
        total_paid = (
            Payment.objects.alive()
            .filter(status="paid")
            .aggregate(total=models.Sum("amount"))["total"]
            or 0
        )
        year_paid = (
            Payment.objects.alive()
            .filter(status="paid", executed_date__gte=year_start)
            .aggregate(total=models.Sum("amount"))["total"]
            or 0
        )
        pending_payments = Payment.objects.alive().filter(status="pending").count()

        consumption_rate = 0
        if total_budget > 0:
            consumption_rate = round((total_paid / total_budget) * 100, 1)

        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "active_rate": round(
                (active_employees / total_employees * 100) if total_employees else 0, 1
            ),
            "total_beneficiaries": total_beneficiaries,
            "beneficiaries_per_employee": (
                round(total_beneficiaries / total_employees, 2) if total_employees else 0
            ),
            "total_benefits": total_benefits,
            "total_benefits_amount": total_benefits_amount,
            "avg_benefit_amount": (
                round(total_benefits_amount / total_benefits, 2) if total_benefits else 0
            ),
            "month_benefits_amount": month_benefits_amount,
            "total_conventions": total_conventions,
            "active_conventions": active_conventions,
            "expired_conventions": expired_conventions,
            "convention_active_rate": round(
                (active_conventions / total_conventions * 100) if total_conventions else 0, 1
            ),
            "total_budget": total_budget,
            "total_paid": total_paid,
            "year_paid": year_paid,
            "consumption_rate": consumption_rate,
            "pending_payments": pending_payments,
            "avg_payment_amount": round(
                total_paid / max(Payment.objects.alive().filter(status="paid").count(), 1), 2
            ),
        }


aggregation_service = AggregationService()
