"""
============================================================
FORECASTING SERVICE — Prévisions budgétaires avancées
============================================================
Méthodes :
  - ARIMA-like (régression linéaire sur fenêtre glissante)
  - Monte Carlo (simulation stochastique)
  - What-if (scénarios paramétriques)
  - Décomposition saisonnière (détection des cycles)
"""

import logging
from datetime import timedelta
from statistics import mean

from django.db.models import Count, Sum
from django.utils import timezone

from .ml.math_utils import (
    linear_regression,
    monte_carlo_simulation,
    seasonal_decompose,
)
from .models import AIModelRegistry, AIPrediction

logger = logging.getLogger("shared.ai.forecasting")


class ForecastingService:
    """Prévisions multi-méthodes."""

    def forecast_budget(
        self,
        months_ahead: int = 6,
        method: str = "ensemble",
        save: bool = True,
    ) -> dict:
        """
        Prévision de consommation budgétaire.
        method : "linear", "monte_carlo", "seasonal", "ensemble"
        """
        from django.apps import apps

        try:
            Payment = apps.get_model("finance", "Payment")
            Budget = apps.get_model("finance", "Budget")
        except LookupError:
            return {"error": "Finance models not available"}

        today = timezone.localdate()
        year = today.year
        total_budget = (
            Budget.objects.filter(
                fiscal_year__year=year,
                is_deleted=False,
            ).aggregate(
                s=Sum("allocated_amount")
            )["s"]
            or 0
        )

        monthly_payments = self._get_monthly_payments(Payment, years=3)
        if not monthly_payments:
            return {"error": "Not enough payment history"}

        values = [float(m["total"]) for m in monthly_payments]
        forecasts = {}

        if method in ("linear", "ensemble"):
            forecasts["linear"] = self._linear_forecast(values, months_ahead)

        if method in ("monte_carlo", "ensemble"):
            mc = monte_carlo_simulation(values, n_simulations=2000, horizon=months_ahead)
            if "error" not in mc:
                forecasts["monte_carlo"] = mc

        if method in ("seasonal", "ensemble") and len(values) >= 24:
            sd = seasonal_decompose(values, period=12)
            if "error" not in sd:
                trend_forecast = self._extend_trend(sd["trend"], months_ahead)
                seasonal = sd["seasonal"][-12:] if len(sd["seasonal"]) >= 12 else [0] * 12
                combined = [
                    trend_forecast[i] + seasonal[i % len(seasonal)] for i in range(months_ahead)
                ]
                forecasts["seasonal"] = {
                    "method": "seasonal_decomposition",
                    "horizon": months_ahead,
                    "forecasts": [
                        {"step": i + 1, "value": round(v, 2)} for i, v in enumerate(combined)
                    ],
                }

        if method == "ensemble" and len(forecasts) > 1:
            forecasts["ensemble"] = self._ensemble_forecast(forecasts, months_ahead)

        result = {
            "target": "budget_consumption",
            "fiscal_year": year,
            "total_budget": total_budget,
            "method": method,
            "horizon_months": months_ahead,
            "historical_months": len(values),
            "forecasts": forecasts,
        }

        if save:
            self._save_forecast(result)

        return result

    def forecast_benefits(
        self,
        months_ahead: int = 6,
        method: str = "ensemble",
    ) -> dict:
        """Prévision du nombre de demandes de prestations."""
        from django.apps import apps

        try:
            Benefit = apps.get_model("benefits", "Benefit")
        except LookupError:
            return {"error": "Benefits models not available"}

        monthly = self._get_monthly_counts(Benefit, months=24)
        if len(monthly) < 3:
            return {"error": "Not enough historical data"}

        values = [float(m["count"]) for m in monthly]
        slope, intercept, r2 = linear_regression(list(range(len(values))), values)

        predictions = []
        for i in range(1, months_ahead + 1):
            x = len(values) + i - 1
            pred = max(0, slope * x + intercept)
            predictions.append(
                {
                    "month": i,
                    "predicted_count": round(pred),
                    "lower_bound": max(0, round(pred * 0.8)),
                    "upper_bound": round(pred * 1.2),
                }
            )

        return {
            "target": "benefits_volume",
            "method": "linear_regression",
            "r_squared": round(r2, 3),
            "trend": "up" if slope > 0 else "down" if slope < 0 else "stable",
            "historical_months": len(values),
            "predictions": predictions,
        }

    def what_if_scenario(self, scenario: dict) -> dict:
        """
        Scénario what-if paramétrique.
        scenario = {"budget_change_pct": -10, "new_hires": 50, ...}
        """

        base = self.forecast_budget(months_ahead=12, method="linear", save=False)
        if "error" in base:
            return base

        adjustment = scenario.get("budget_change_pct", 0) / 100
        new_hires_cost = scenario.get("new_hires", 0) * scenario.get("cost_per_hire", 50000)

        adjusted = []
        for f in base.get("forecasts", {}).get("linear", {}).get("forecasts", []):
            val = f.get("value", 0)
            val += val * adjustment
            val += new_hires_cost / 12
            adjusted.append(
                {"step": f["step"], "base": f.get("value", 0), "adjusted": round(val, 2)}
            )

        return {
            "scenario": scenario,
            "impact": {
                "budget_change": f"{scenario.get('budget_change_pct', 0):+.0f}%",
                "new_annual_cost": new_hires_cost * 12,
            },
            "adjusted_forecasts": adjusted,
        }

    def _get_monthly_payments(self, Payment, years: int = 3) -> list[dict]:
        today = timezone.localdate()
        start = today.replace(year=today.year - years, month=1, day=1)
        return list(
            Payment.objects.filter(
                executed_date__gte=start,
                status="paid",
                is_deleted=False,
            )
            .extra(
                {
                    "year": "EXTRACT(year FROM executed_date)",
                    "month": "EXTRACT(month FROM executed_date)",
                }
            )
            .values("year", "month")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("year", "month")
        )

    def _get_monthly_counts(self, Model, months: int = 24) -> list[dict]:
        since = timezone.now() - timedelta(days=months * 31)
        return list(
            Model.objects.filter(created_at__gte=since, is_deleted=False)
            .extra(
                {"year": "EXTRACT(year FROM created_at)", "month": "EXTRACT(month FROM created_at)"}
            )
            .values("year", "month")
            .annotate(count=Count("id"))
            .order_by("year", "month")
        )

    def _linear_forecast(self, values: list[float], horizon: int) -> dict:
        xs = list(range(len(values)))
        slope, intercept, r2 = linear_regression(xs, values)
        preds = []
        for i in range(1, horizon + 1):
            x = len(values) + i - 1
            preds.append({"step": i, "value": round(max(0, slope * x + intercept), 2)})
        return {
            "method": "linear_regression",
            "r_squared": round(r2, 3),
            "slope": round(slope, 2),
            "horizon": horizon,
            "forecasts": preds,
        }

    def _extend_trend(self, trend: list[float], steps: int) -> list[float]:
        if len(trend) < 2:
            return [0] * steps
        valid = [(i, v) for i, v in enumerate(trend) if v is not None]
        if len(valid) < 2:
            return [trend[-1] or 0] * steps if trend else [0] * steps
        xs = [v[0] for v in valid]
        ys = [v[1] for v in valid]
        slope, intercept, _ = linear_regression(xs, ys)
        return [slope * (len(trend) + i) + intercept for i in range(steps)]

    def _ensemble_forecast(self, forecasts: dict, horizon: int) -> dict:
        combined = []
        for step in range(1, horizon + 1):
            vals = []
            for f in forecasts.values():
                fcasts = f.get("forecasts", [])
                for fc in fcasts:
                    if fc.get("step") == step:
                        vals.append(fc.get("value", 0))
            avg = mean(vals) if vals else 0
            combined.append({"step": step, "value": round(avg, 2), "n_models": len(vals)})
        return {"method": "ensemble", "horizon": horizon, "forecasts": combined}

    def _save_forecast(self, result: dict):
        model, _ = AIModelRegistry.objects.get_or_create(
            name="forecasting_engine_v1",
            defaults={"version": "1.0.0", "task_type": "forecast", "status": "production"},
        )
        AIPrediction.objects.create(
            model=model,
            prediction_type="budget_forecast",
            target_type="Budget",
            output_data=result,
            confidence=0.7,
        )


forecasting_service = ForecastingService()
