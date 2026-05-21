"""
============================================================
SCORING ENGINE — Scoring de demandes avec explicabilité
============================================================
Calcule des scores 0-100 avec feature importance (SHAP-like)
pour les demandes de prestations, profils de risque, etc.
"""

import logging

from django.utils import timezone

from .models import AIModelRegistry, AIScore

logger = logging.getLogger("shared.ai.scoring")


class ScoringEngine:
    """
    Moteur de scoring ML-ready.

    Chaque score est accompagné de :
      - feature_importance : contribution de chaque feature au score
      - explanation : texte lisible
      - decision_boundary : seuil de classification
    """

    def score_benefit(self, benefit_id, save=False) -> dict:
        """Calcule le score d'une demande de prestation."""
        from django.apps import apps

        Benefit = apps.get_model("benefits", "Benefit")
        if isinstance(benefit_id, Benefit):
            benefit = benefit_id
        else:
            benefit = Benefit.objects.get(pk=benefit_id)

        features = self._extract_benefit_features(benefit)
        score, importance = self._compute_score(features)

        explanation_parts = []
        for name, contrib in sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
            direction = "augmente" if contrib > 0 else "diminue"
            explanation_parts.append(f"« {name} » {direction} le score de {abs(contrib):.1f} pts")

        result = {
            "score": round(score, 1),
            "confidence": round(min(abs(score - 50) / 50, 1.0), 2),
            "features": features,
            "feature_importance": importance,
            "explanation": "; ".join(explanation_parts[:3])
            or "Score basé sur les critères standards.",
            "decision_boundary": 50.0,
            "risk_level": (
                "low"
                if score < 30
                else "medium" if score < 60 else "high" if score < 80 else "critical"
            ),
            "recommendation": (
                "À valider rapidement"
                if score < 30
                else (
                    "Vérification standard"
                    if score < 60
                    else "Inspection requise" if score < 80 else "Refus recommandé"
                )
            ),
        }
        if save:
            self.save_score(result, "Benefit", str(benefit.pk), str(benefit))
        return result

    def score_employee_risk(self, employee) -> dict:
        """Calcule le score de risque d'un employé."""
        features = self._extract_employee_risk_features(employee)
        score, importance = self._compute_risk_score(features)

        return {
            "score": round(score, 1),
            "confidence": round(min(abs(score - 50) / 50, 1.0), 2),
            "features": features,
            "feature_importance": importance,
            "risk_level": "low" if score < 30 else "medium" if score < 60 else "high",
            "recommendation": (
                "Aucune action"
                if score < 30
                else "Surveillance" if score < 60 else "Vérification recommandée"
            ),
        }

    def score_budget_risk(self, budget_line) -> dict:
        """Calcule le score de risque de dépassement budgétaire."""
        from django.apps import apps

        Payment = apps.get_model("finance", "Payment")

        total_budget = float(budget_line.amount or 0)
        paid = float(
            Payment.objects.filter(
                budget_line=budget_line,
                status="paid",
                is_deleted=False,
            ).aggregate(total=sum)["total"]
            or 0
        )

        today = timezone.localdate()
        year_start = today.replace(month=1, day=1)
        days_elapsed = (today - year_start).days or 1
        days_total = 366 if today.year % 4 == 0 else 365
        progress = days_elapsed / days_total

        consumption_rate = paid / total_budget if total_budget else 0
        expected_rate = progress
        variance = consumption_rate - expected_rate

        score = min(100, max(0, 50 + variance * 100))
        importance = {
            "consumption_rate": round(consumption_rate * 100 - expected_rate * 100, 1),
            "remaining_budget": round(total_budget - paid, 2),
            "time_progress": round(progress * 100, 1),
            "burn_rate": round(paid / max(days_elapsed, 1), 2),
        }

        return {
            "score": round(score, 1),
            "confidence": 0.7,
            "features": {
                "total_budget": total_budget,
                "paid": paid,
                "consumption_rate": consumption_rate,
                "expected_rate": expected_rate,
            },
            "feature_importance": importance,
            "risk_level": (
                "critical"
                if score > 80
                else "high" if score > 60 else "medium" if score > 40 else "low"
            ),
            "recommendation": (
                "Freiner les dépenses" if score > 60 else "Surveiller" if score > 40 else "Normal"
            ),
        }

    def _extract_benefit_features(self, benefit) -> dict[str, float]:
        features = {}
        features["amount"] = float(benefit.requested_amount or 0)

        # Type-based risk
        if hasattr(benefit, "benefit_type") and benefit.benefit_type:
            features["type_id"] = float(hash(benefit.benefit_type_id) % 100) / 100

        # Employee tenure
        if benefit.employee and benefit.employee.date_of_birth:
            features["employee_age"] = round(
                (timezone.localdate() - benefit.employee.date_of_birth).days / 365.25, 1
            )
        else:
            features["employee_age"] = 35.0

        # Previous benefits count
        if benefit.employee and hasattr(benefit.employee, "benefits"):
            prev_count = benefit.employee.benefits.filter(is_deleted=False).count()
            features["previous_benefits"] = prev_count
        else:
            features["previous_benefits"] = 0

        # Workflow history
        if hasattr(benefit, "analytics_data") and benefit.analytics_data:
            total_hours = sum(
                v for v in benefit.analytics_data.values() if isinstance(v, int | float)
            )
            features["processing_time_hours"] = total_hours
        else:
            features["processing_time_hours"] = 0

        # Has attachments
        if hasattr(benefit, "attachments"):
            features["has_attachments"] = 1 if benefit.attachments.alive().count() > 0 else 0
        else:
            features["has_attachments"] = 0

        return features

    def _extract_employee_risk_features(self, employee) -> dict[str, float]:
        features = {}
        if employee.date_of_birth:
            features["age"] = round(
                (timezone.localdate() - employee.date_of_birth).days / 365.25, 1
            )
        features["status"] = (
            1.0 if employee.status == "suspended" else 0.5 if employee.status == "inactive" else 0.0
        )
        beneficiaries_count = 0
        if hasattr(employee, "beneficiaries"):
            beneficiaries_count = employee.beneficiaries.filter(is_deleted=False).count()
        features["beneficiaries_count"] = beneficiaries_count
        benefits_count = 0
        if hasattr(employee, "benefits"):
            benefits_count = employee.benefits.filter(is_deleted=False).count()
        features["benefits_history"] = benefits_count
        return features

    def _compute_score(self, features: dict[str, float]) -> tuple[float, dict[str, float]]:
        """
        Calcule le score avec feature importance linéaire.
        Importance = contribution de chaque feature normalisée.
        """
        weights = {
            "amount": 0.30,
            "employee_age": 0.10,
            "previous_benefits": 0.20,
            "processing_time_hours": 0.15,
            "has_attachments": 0.15,
            "type_id": 0.10,
        }
        raw_score = 0.0
        contributions = {}
        for name, weight in weights.items():
            val = features.get(name, 0)
            norm = self._normalize(name, val)
            contrib = weight * norm * 100
            contributions[name] = round(contrib, 2)
            raw_score += contrib

        score = max(0, min(100, raw_score))
        return score, contributions

    def _compute_risk_score(self, features: dict[str, float]) -> tuple[float, dict[str, float]]:
        weights = {
            "age": 0.15,
            "status": 0.40,
            "beneficiaries_count": 0.20,
            "benefits_history": 0.25,
        }
        raw_score = 0.0
        contributions = {}
        for name, weight in weights.items():
            val = features.get(name, 0)
            norm = self._normalize(name, val)
            contrib = weight * norm * 100
            contributions[name] = round(contrib, 2)
            raw_score += contrib
        return max(0, min(100, raw_score)), contributions

    def _normalize(self, name: str, value: float) -> float:
        norms = {
            "amount": lambda v: min(v / 500000, 1.0),
            "employee_age": lambda v: min(v / 70, 1.0),
            "previous_benefits": lambda v: min(v / 20, 1.0),
            "processing_time_hours": lambda v: min(v / 168, 1.0),
            "has_attachments": lambda v: v,
            "type_id": lambda v: v,
            "age": lambda v: min(v / 70, 1.0),
            "status": lambda v: v,
            "beneficiaries_count": lambda v: min(v / 10, 1.0),
            "benefits_history": lambda v: min(v / 30, 1.0),
        }
        normalizer = norms.get(name, lambda v: min(v / 100, 1.0))
        return normalizer(value)

    def save_score(
        self, score_data: dict, target_type: str, target_id: str, target_repr: str = ""
    ) -> AIScore:
        model, _ = AIModelRegistry.objects.get_or_create(
            name="scoring_engine_v1",
            defaults={"version": "1.0.0", "task_type": "scoring", "status": "production"},
        )
        return AIScore.objects.create(
            model=model,
            score_type="demand" if "Benefit" in target_type else "risk",
            target_type=target_type,
            target_id=target_id,
            target_repr=target_repr,
            score=score_data["score"],
            confidence=score_data.get("confidence"),
            features=score_data.get("features", {}),
            feature_importance=score_data.get("feature_importance", {}),
            explanation=score_data.get("explanation", ""),
            decision_boundary=score_data.get("decision_boundary"),
            recommendation=score_data.get("recommendation", ""),
        )


scoring_engine = ScoringEngine()
