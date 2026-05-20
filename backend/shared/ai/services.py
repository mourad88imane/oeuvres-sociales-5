"""
AI / Prediction services for reporting module.

Provides statistical forecasts, anomaly detection, and decision support
using historical KPI data. Pure Python — no ML libraries required.
"""
import logging
import math
from datetime import date, timedelta
from statistics import mean, stdev

from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone

logger = logging.getLogger("shared.ai")


def _linear_regression(xs, ys):
    """Ordinary least-squares: returns (slope, intercept, r_squared)."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0), 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den else 0.0
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot else 0.0
    return slope, intercept, r2


def _zscore_anomalies(values, threshold=2.0):
    """Return list of (index, value, zscore) for values beyond threshold."""
    if len(values) < 3:
        return []
    m = mean(values)
    s = stdev(values)
    if s == 0:
        return []
    return [(i, v, (v - m) / s) for i, v in enumerate(values) if abs((v - m) / s) > threshold]


class PredictionService:
    """Statistical predictions and decision support using historical data."""

    # ── Trend prediction ────────────────────────────────────

    _aggregation_service = None

    @property
    def aggr(self):
        """Resolve aggregation service lazily — allows overriding per project."""
        if self._aggregation_service is None:
            try:
                from django.conf import settings
                svc = getattr(settings, "AI_AGGREGATION_SERVICE", None)
                if svc:
                    from django.utils.module_loading import import_string
                    self._aggregation_service = import_string(svc)
                else:
                    from apps.reporting.services import aggregation_service
                    self._aggregation_service = aggregation_service
            except ImportError:
                from apps.reporting.services import aggregation_service
                self._aggregation_service = aggregation_service
        return self._aggregation_service

    @staticmethod
    def _get_model(model_path: str):
        """Resolve a Django model dynamically from a dotted path."""
        from django.apps import apps
        try:
            return apps.get_model(model_path)
        except LookupError:
            raise ImportError(f"Model '{model_path}' not found. Ensure the containing app is in INSTALLED_APPS.")

    def predict_benefits_trend(self, months_ahead=3):
        """
        Predict monthly benefits count & amount for the next N months
        using linear regression on the past 12 months of data.
        """
        trends = self.aggr.get_monthly_trends(months=12)
        if not trends:
            return {"error": "Not enough historical data"}

        n = len(trends)
        xs = list(range(n))
        counts = [t.get("benefits_count", 0) for t in trends]
        amounts = [float(t.get("benefits_amount", 0)) for t in trends]

        slope_c, intercept_c, _ = _linear_regression(xs, counts)
        slope_a, intercept_a, _ = _linear_regression(xs, amounts)

        predictions = []
        last_month = trends[-1]["month"]
        for i in range(1, months_ahead + 1):
            # Estimate next month label
            y, m = int(last_month[:4]), int(last_month[5:7])
            m += i
            if m > 12:
                m -= 12
                y += 1
            label = f"{y}-{m:02d}"

            x = n + i - 1
            pred_count = max(0, round(slope_c * x + intercept_c))
            pred_amount = max(0, slope_a * x + intercept_a)

            predictions.append({
                "month": label,
                "predicted_count": pred_count,
                "predicted_amount": round(pred_amount, 2),
                "confidence": round(min(abs(slope_c) * 10, 100), 1),
            })

        return {
            "target": "benefits",
            "period": f"{months_ahead}m",
            "baseline_months": n,
            "predictions": predictions,
        }

    def predict_budget_consumption(self):
        """
        Project year-end budget consumption based on current spend rate.
        Uses real Payment data vs Budget totals.
        """
        from django.apps import apps

        Budget = apps.get_model("finance", "Budget")
        Payment = apps.get_model("finance", "Payment")

        today = timezone.localdate()
        year_start = today.replace(month=1, day=1)
        days_elapsed = (today - year_start).days or 1
        days_total = 366 if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0) else 365
        progress_pct = min(days_elapsed / days_total, 1.0)

        budgets = Budget.objects.filter(
            fiscal_year__year=today.year, is_deleted=False
        )
        total_budget = budgets.aggregate(total=Sum("amount"))["total"] or 0

        paid = Payment.objects.filter(
            is_deleted=False, executed_date__year=today.year, status="paid"
        ).aggregate(total=Sum("amount"))["total"] or 0

        current_rate = (paid / total_budget * 100) if total_budget else 0
        projected_rate = current_rate / progress_pct if progress_pct else 0
        projected_amount = total_budget * (projected_rate / 100)

        risk = "critical"
        if projected_rate < 70:
            risk = "low"
        elif projected_rate < 85:
            risk = "moderate"
        elif projected_rate < 100:
            risk = "elevated"

        return {
            "fiscal_year": today.year,
            "total_budget": total_budget,
            "paid_to_date": paid,
            "consumption_rate": round(current_rate, 1),
            "projected_rate": round(min(projected_rate, 200), 1),
            "projected_amount": round(projected_amount, 2),
            "days_progress_pct": round(progress_pct * 100, 1),
            "risk_level": risk,
            "recommendation": (
                "Ralentir les dépenses" if risk == "critical"
                else "Maintenir le rythme" if risk == "low"
                else "Surveiller le budget"
            ),
        }

    # ── Anomaly detection ──────────────────────────────────

    def detect_anomalies(self, days=90):
        """
        Scan KpiSnapshot history for anomalous values using z-score.
        Returns list of anomalies detected across all KPIs.
        """
        KpiDef = self._get_model("reporting.KpiDefinition")
        KpiSnap = self._get_model("reporting.KpiSnapshot")

        anomalies = []
        cutoff = timezone.localdate() - timedelta(days=days)
        kpis = KpiDef.objects.filter(is_active=True)

        for kpi in kpis:
            snapshots = KpiSnap.objects.filter(
                kpi=kpi, date__gte=cutoff
            ).order_by("date").values_list("value", flat=True)

            if len(snapshots) < 5:
                continue

            hits = _zscore_anomalies(list(snapshots), threshold=2.0)
            for idx, val, z in hits:
                anomalies.append({
                    "kpi_code": kpi.code,
                    "kpi_name": kpi.name,
                    "category": kpi.category,
                    "value": val,
                    "zscore": round(z, 2),
                    "severity": "high" if abs(z) > 3 else "medium",
                    "date": str(timezone.localdate() - timedelta(days=days - idx)),
                })

        anomalies.sort(key=lambda a: abs(a["zscore"]), reverse=True)
        return {
            "period_days": days,
            "total_anomalies": len(anomalies),
            "anomalies": anomalies[:20],
        }

    # ── Decision support ────────────────────────────────────

    def decision_support(self):
        """
        Rule-based recommendations drawn from current KPI values,
        budget health, convention expiry risks, and workflow backlogs.
        """
        today = timezone.localdate()
        kpis = self.aggr.get_all_kpis()
        kpi_map = {k["code"]: k for k in kpis}
        recommendations = []

        # 1. Budget consumption check
        budget_info = self.predict_budget_consumption()
        if budget_info.get("risk_level") == "critical":
            recommendations.append({
                "domain": "finance",
                "priority": "high",
                "title": "Risque de dépassement budgétaire",
                "detail": (
                    f"Consommation projetée à {budget_info['projected_rate']:.0f}% "
                    f"({budget_info['fiscal_year']}). Action recommandée : "
                    f"{budget_info['recommendation']}."
                ),
            })

        # 2. Convention expiry alerts
        try:
            Convention = apps.get_model("conventions", "Convention")
            expiring = Convention.objects.alive().filter(
                end_date__gte=today, end_date__lte=today + timedelta(days=30)
            ).count()
            if expiring > 0:
                recommendations.append({
                    "domain": "conventions",
                    "priority": "high" if expiring > 5 else "medium",
                    "title": "Conventions arrivant à expiration",
                    "detail": (
                        f"{expiring} convention(s) expirent dans les 30 prochains jours. "
                        "Prévoir les renouvellements."
                    ),
                })
        except LookupError:
            pass

        # 3. Benefits backlog
        benefits_kpi = kpi_map.get("pending_benefits", {})
        pending = benefits_kpi.get("current_value", 0)
        if pending > 50:
            recommendations.append({
                "domain": "benefits",
                "priority": "high" if pending > 100 else "medium",
                "title": "Backlog de prestations",
                "detail": (
                    f"{int(pending)} prestations en attente de traitement. "
                    "Envisager un renfort ou une priorisation."
                ),
            })
        elif pending > 10:
            recommendations.append({
                "domain": "benefits",
                "priority": "low",
                "title": "Prestations en attente",
                "detail": f"{int(pending)} dossiers à traiter.",
            })

        # 4. KPI target deviation
        for kpi in kpis:
            cv = kpi.get("current_value")
            tv = kpi.get("target_value")
            if cv is not None and tv and tv > 0:
                deviation = abs(cv - tv) / tv
                if deviation > 0.2:
                    recommendations.append({
                        "domain": kpi.get("category", "global"),
                        "priority": "medium",
                        "title": f"Écart significatif : {kpi['name']}",
                        "detail": (
                            f"Valeur actuelle {cv:.0f} vs objectif {tv:.0f} "
                            f"(écart {deviation:.0%})."
                        ),
                    })

        # 5. New employee surge
        try:
            Employee = apps.get_model("employees", "Employee")
            month_start = today.replace(day=1)
            new_emp = Employee.objects.alive().filter(
                created_at__date__gte=month_start
            ).count()
            if new_emp > 20:
                recommendations.append({
                    "domain": "hr",
                    "priority": "low",
                    "title": "Afflux de nouveaux employés",
                    "detail": (
                        f"{new_emp} employés recrutés ce mois-ci. "
                        "Vérifier l'enregistrement des ayants droit."
                    ),
                })
        except LookupError:
            pass

        recommendations.sort(
            key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 3)
        )

        return {
            "generated_at": str(today),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
        }
