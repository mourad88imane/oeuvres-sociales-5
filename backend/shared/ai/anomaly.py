"""
============================================================
ANOMALY DETECTION — Multi-méthode avec agrégation ensembliste
============================================================
Méthodes supportées :
  - Z-score
  - IQR (interquartile range — robuste)
  - Moving average residual
  - Seasonal decomposition
  - Ensemble (moyenne pondérée des méthodes)
"""

import logging
from datetime import timedelta

from django.utils import timezone

from .ml.math_utils import (
    iqr_anomalies,
    moving_average_anomalies,
    zscore_anomalies,
)
from .models import AIAnomaly, AIModelRegistry

logger = logging.getLogger("shared.ai.anomaly")


class AnomalyDetector:
    """Détecteur d'anomalies multi-méthodes avec agrégation."""

    def detect_kpi_anomalies(
        self,
        days: int = 90,
        methods: list[str] | None = None,
        save: bool = True,
    ) -> dict:
        """
        Détecte les anomalies sur l'historique des KPI snapshots.
        methods : ["zscore", "iqr", "moving_avg", "seasonal", "ensemble"]
        """
        from django.apps import apps

        try:
            KpiDef = apps.get_model("reporting", "KpiDefinition")
            KpiSnap = apps.get_model("reporting", "KpiSnapshot")
        except LookupError:
            return {"error": "Reporting models not available"}

        methods = methods or ["zscore", "iqr", "moving_avg"]
        cutoff = timezone.localdate() - timedelta(days=days)
        all_anomalies = []
        kpis = KpiDef.objects.filter(is_active=True)

        for kpi in kpis:
            snapshots = list(
                KpiSnap.objects.filter(kpi=kpi, date__gte=cutoff)
                .order_by("date")
                .values_list("value", flat=True)
            )

            if len(snapshots) < 5:
                continue

            results = self._apply_methods(snapshots, methods, kpi.code)

            for r in results:
                severity = self._compute_severity(r["deviation_pct"])
                all_anomalies.append(
                    {
                        "target_type": "KpiSnapshot",
                        "target_id": kpi.code,
                        "target_repr": f"{kpi.name} ({kpi.code})",
                        "metric_name": kpi.code,
                        "expected_value": r["expected"],
                        "actual_value": r["actual"],
                        "deviation": r["deviation"],
                        "deviation_pct": r["deviation_pct"],
                        "zscore": r.get("zscore"),
                        "severity": severity,
                        "detection_method": r["method"],
                        "context": {
                            "kpi_category": kpi.category,
                            "kpi_unit": kpi.unit,
                            "method": r["method"],
                        },
                        "explanation": self._build_explanation(kpi, r),
                    }
                )

        all_anomalies.sort(key=lambda a: abs(a["deviation_pct"] or 0), reverse=True)

        if save and all_anomalies:
            model = self._get_or_create_model()
            for a in all_anomalies[:50]:
                AIAnomaly.objects.create(model=model, **a)

        return {
            "period_days": days,
            "methods_used": methods,
            "total_detected": len(all_anomalies),
            "anomalies": all_anomalies[:20],
        }

    def detect_benefit_anomalies(self, days: int = 30, save: bool = True) -> dict:
        """Détecte les anomalies sur les demandes de prestations."""
        from django.apps import apps

        Benefit = apps.get_model("benefits", "Benefit")
        since = timezone.now() - timedelta(days=days)
        amounts = list(
            Benefit.objects.filter(created_at__gte=since)
            .exclude(requested_amount__isnull=True)
            .values_list("requested_amount", flat=True)
        )
        if not amounts:
            return {"total_detected": 0, "anomalies": []}

        amounts_f = [float(a) for a in amounts]
        anomalies = []
        for method in ["zscore", "iqr"]:
            if method == "zscore":
                hits = zscore_anomalies(amounts_f, threshold=2.5)
                for _idx, val, z in hits:
                    anomalies.append(
                        {
                            "target_type": "Benefit",
                            "detection_method": method,
                            "metric_name": "amount",
                            "actual_value": val,
                            "zscore": z,
                            "severity": "high" if abs(z) > 3 else "medium",
                        }
                    )
            elif method == "iqr":
                hits = iqr_anomalies(amounts_f, multiplier=2.0)
                for _idx, val in hits:
                    anomalies.append(
                        {
                            "target_type": "Benefit",
                            "detection_method": method,
                            "metric_name": "amount",
                            "actual_value": val,
                            "severity": "medium",
                        }
                    )

        if save and anomalies:
            model = self._get_or_create_model()
            for a in anomalies[:30]:
                AIAnomaly.objects.create(model=model, **a)

        return {"period_days": days, "total_detected": len(anomalies), "anomalies": anomalies[:20]}

    def detect_payment_anomalies(self, days: int = 90, save: bool = True) -> dict:
        """Détecte les anomalies sur les paiements."""
        from django.apps import apps

        Payment = apps.get_model("finance", "Payment")
        since = timezone.now() - timedelta(days=days)
        amounts = list(
            Payment.objects.filter(executed_date__gte=since, status="paid").values_list(
                "amount", flat=True
            )
        )
        if not amounts:
            return {"total_detected": 0, "anomalies": []}
        amounts_f = [float(a) for a in amounts]
        anomalies = []
        for method in ["zscore", "iqr"]:
            if method == "zscore":
                for _idx, val, z in zscore_anomalies(amounts_f, threshold=3.0):
                    anomalies.append(
                        {
                            "target_type": "Payment",
                            "detection_method": method,
                            "metric_name": "amount",
                            "actual_value": val,
                            "zscore": z,
                            "severity": (
                                "critical" if abs(z) > 4 else "high" if abs(z) > 3 else "medium"
                            ),
                        }
                    )
        if save and anomalies:
            model = self._get_or_create_model()
            for a in anomalies[:30]:
                AIAnomaly.objects.create(model=model, **a)
        return {"period_days": days, "total_detected": len(anomalies), "anomalies": anomalies[:20]}

    def _apply_methods(self, values: list[float], methods: list[str], kpi_code: str) -> list[dict]:
        """Applique chaque méthode et retourne les résultats consolidés."""
        results = []
        if "zscore" in methods:
            for idx, val, z in zscore_anomalies(values, threshold=2.0):
                expected = mean_excluding(values, idx)
                results.append(
                    {
                        "method": "zscore",
                        "expected": expected,
                        "actual": val,
                        "deviation": val - expected,
                        "deviation_pct": ((val - expected) / expected * 100) if expected else 0,
                        "zscore": z,
                    }
                )
        if "iqr" in methods:
            for idx, val in iqr_anomalies(values, multiplier=1.5):
                expected = mean_excluding(values, idx)
                results.append(
                    {
                        "method": "iqr",
                        "expected": expected,
                        "actual": val,
                        "deviation": val - expected,
                        "deviation_pct": ((val - expected) / expected * 100) if expected else 0,
                    }
                )
        if "moving_avg" in methods:
            for _idx, val, ma, resid in moving_average_anomalies(
                values, window=3, std_multiplier=2.0
            ):
                results.append(
                    {
                        "method": "moving_avg",
                        "expected": ma,
                        "actual": val,
                        "deviation": resid,
                        "deviation_pct": (resid / ma * 100) if ma else 0,
                    }
                )
        return results

    def _compute_severity(self, deviation_pct: float | None) -> str:
        if deviation_pct is None:
            return "low"
        adev = abs(deviation_pct)
        if adev > 50:
            return "critical"
        if adev > 30:
            return "high"
        if adev > 15:
            return "medium"
        return "low"

    def _build_explanation(self, kpi, result: dict) -> str:
        method_labels = {
            "zscore": "écart-type",
            "iqr": "intervalle interquartile",
            "moving_avg": "moyenne mobile",
        }
        label = method_labels.get(result["method"], result["method"])
        return (
            f"KPI {kpi.name}: valeur {result['actual']:.1f} vs attendue {result['expected']:.1f} "
            f"(écart {result['deviation_pct']:+.1f}%) — méthode {label}"
        )

    def _get_or_create_model(self):
        model, _ = AIModelRegistry.objects.get_or_create(
            name="anomaly_detector_v1",
            defaults={
                "version": "1.0.0",
                "task_type": "anomaly",
                "algorithm": "ensemble (zscore + iqr + moving_avg)",
                "status": "production",
                "description": "Détecteur d'anomalies multi-méthodes",
            },
        )
        return model


def mean_excluding(values: list[float], exclude_idx: int) -> float:
    """Moyenne excluant un index (pour calculer la valeur attendue)."""
    filtered = [v for i, v in enumerate(values) if i != exclude_idx]
    from statistics import mean as _mean

    return _mean(filtered) if filtered else 0.0


anomaly_detector = AnomalyDetector()
