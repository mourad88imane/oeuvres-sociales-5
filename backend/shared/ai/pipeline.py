"""
============================================================
AI PIPELINE — Collecte, transformation, feature engineering
============================================================
Pipeline de données pour le ML :
  1. Collecte des données brutes (collectors)
  2. Transformation et cleaning
  3. Feature engineering
  4. Stockage dans le feature store (AIFeature)
"""

import logging
from datetime import timedelta
from typing import Any

from django.db.models import Avg, Count, Sum
from django.utils import timezone

logger = logging.getLogger("shared.ai.pipeline")


class DataCollector:
    """Collecte les données brutes depuis les modèles métier."""

    @staticmethod
    def _get_model(model_path: str):
        from django.apps import apps

        try:
            return apps.get_model(model_path)
        except LookupError:
            raise ImportError(f"Model '{model_path}' not found.")

    def collect_benefits_stats(self, days: int = 90) -> dict[str, Any]:
        Benefit = self._get_model("benefits.Benefit")
        self._get_model("benefits.BenefitType")
        since = timezone.now() - timedelta(days=days)
        qs = Benefit.objects.filter(created_at__gte=since)
        by_type = list(
            qs.values("benefit_type__name")
            .annotate(count=Count("id"), total_amount=Sum("requested_amount"))
            .order_by("-count")
        )
        by_status = list(qs.values("workflow_state").annotate(count=Count("id")).order_by("-count"))
        return {
            "period_days": days,
            "total": qs.count(),
            "by_type": by_type,
            "by_status": by_status,
            "pending": qs.filter(workflow_state__in=["submitted", "under_review"]).count(),
            "avg_amount": qs.aggregate(avg=Avg("requested_amount"))["avg"] or 0,
        }

    def collect_finance_stats(self, year: int | None = None) -> dict[str, Any]:
        Budget = self._get_model("finance.Budget")
        Payment = self._get_model("finance.Payment")
        year = year or timezone.now().year
        budgets = Budget.objects.filter(fiscal_year__year=year)
        payments = Payment.objects.filter(executed_date__year=year)
        return {
            "year": year,
            "total_budget": budgets.aggregate(s=Sum("allocated_amount"))["s"] or 0,
            "total_paid": payments.filter(status="paid").aggregate(s=Sum("amount"))["s"] or 0,
            "payment_count": payments.count(),
            "pending_payments": payments.filter(status__in=["pending", "approved"]).count(),
        }

    def collect_employee_stats(self) -> dict[str, Any]:
        Employee = self._get_model("employees.Employee")
        total = Employee.objects.alive().count()
        by_status = list(
            Employee.objects.alive().values("status").annotate(count=Count("id")).order_by("-count")
        )
        by_dept = list(
            Employee.objects.alive()
            .values("department__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return {
            "total": total,
            "by_status": by_status,
            "by_department": by_dept,
        }

    def collect_convention_stats(self) -> dict[str, Any]:
        Convention = self._get_model("conventions.Convention")
        today = timezone.localdate()
        active = Convention.objects.alive().filter(status__in=["active", "expiring_soon"]).count()
        expiring_30 = (
            Convention.objects.alive()
            .filter(end_date__gte=today, end_date__lte=today + timedelta(days=30))
            .count()
        )
        return {
            "active": active,
            "expiring_30_days": expiring_30,
            "total_partners": Convention.objects.alive().values("partner").distinct().count(),
        }


class FeatureTransformer:
    """Transforme les données brutes en features ML."""

    def compute_benefit_features(self, benefit) -> dict[str, float]:
        features = {}
        now = timezone.now()
        created = benefit.created_at
        age_days = (now - created).days if created else 0
        features["age_days"] = age_days
        features["amount"] = float(benefit.requested_amount or 0)

        # Workflow velocity features
        if hasattr(benefit, "analytics_data") and benefit.analytics_data:
            ad = benefit.analytics_data
            durations = [v for k, v in ad.items() if k.endswith("_duration_hours")]
            features["avg_state_duration_hours"] = (
                sum(durations) / len(durations) if durations else 0
            )
            features["total_processing_hours"] = sum(durations)
            features["state_transition_count"] = len(ad)
        else:
            features["avg_state_duration_hours"] = 0
            features["total_processing_hours"] = 0
            features["state_transition_count"] = 0

        return features

    def compute_employee_features(self, employee) -> dict[str, float]:
        features = {}
        features["age"] = 0
        if employee.date_of_birth:
            features["age"] = (timezone.localdate() - employee.date_of_birth).days / 365.25
        features["has_beneficiaries"] = (
            1
            if hasattr(employee, "beneficiaries") and employee.beneficiaries.alive().count() > 0
            else 0
        )
        beneficiaries_count = 0
        if hasattr(employee, "beneficiaries"):
            beneficiaries_count = employee.beneficiaries.filter(is_deleted=False).count()
        features["beneficiaries_count"] = beneficiaries_count
        benefits_count = 0
        if hasattr(employee, "benefits"):
            benefits_count = employee.benefits.filter(is_deleted=False).count()
        features["benefits_count"] = benefits_count
        return features


class FeatureStore:
    """Stocke et récupère les features dans AIFeature."""

    def get_feature(self, entity_type: str, entity_id: str, feature_name: str) -> Any | None:
        from ..models import AIFeature

        try:
            f = AIFeature.objects.filter(
                entity_type=entity_type, entity_id=str(entity_id), feature_name=feature_name
            ).latest("computed_at")
            if f.feature_type == "numeric":
                return f.value_numeric
            return f.value_text or f.value_bool or f.value_json
        except AIFeature.DoesNotExist:
            return None

    def set_feature(
        self,
        entity_type: str,
        entity_id: str,
        feature_name: str,
        value,
        ftype: str = "numeric",
        source: str = "pipeline",
    ):
        from ..models import AIFeature

        kwargs = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "feature_name": feature_name,
            "feature_type": ftype,
            "source": source,
        }
        if ftype == "numeric":
            kwargs["value_numeric"] = float(value)
        elif ftype == "text":
            kwargs["value_text"] = str(value)
        elif ftype == "boolean":
            kwargs["value_bool"] = bool(value)
        else:
            kwargs["value_json"] = value
        AIFeature.objects.create(**kwargs)

    def get_entity_features(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        from ..models import AIFeature

        features = AIFeature.objects.filter(
            entity_type=entity_type, entity_id=str(entity_id)
        ).order_by("-computed_at")
        result = {}
        seen = set()
        for f in features:
            if f.feature_name not in seen:
                seen.add(f.feature_name)
                if f.feature_type == "numeric":
                    result[f.feature_name] = f.value_numeric
                elif f.feature_type == "text":
                    result[f.feature_name] = f.value_text
                elif f.feature_type == "boolean":
                    result[f.feature_name] = f.value_bool
                else:
                    result[f.feature_name] = f.value_json
        return result


class AIPipeline:
    """Pipeline IA complet : collecte → transformation → stockage."""

    def __init__(self):
        self.collector = DataCollector()
        self.transformer = FeatureTransformer()
        self.store = FeatureStore()

    def run_benefit_pipeline(self, benefit) -> dict[str, float]:
        features = self.transformer.compute_benefit_features(benefit)
        for name, value in features.items():
            self.store.set_feature("Benefit", str(benefit.pk), name, value)
        return features

    def run_employee_pipeline(self, employee) -> dict[str, float]:
        features = self.transformer.compute_employee_features(employee)
        for name, value in features.items():
            self.store.set_feature("Employee", str(employee.pk), name, value)
        return features


ai_pipeline = AIPipeline()
feature_store = FeatureStore()
data_collector = DataCollector()
