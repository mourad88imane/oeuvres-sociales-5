"""
============================================================
RECOMMENDATION ENGINE — Règles + collaboration + feedback
============================================================
Trois niveaux :
  1. Règles métier (décisionnel)
  2. Collaboration (basé sur l'historique)
  3. Content-based (similarité de profil)

Avec boucle de feedback utilisateur.
"""
import logging
from datetime import date, timedelta
from typing import Optional

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from .models import AIRecommendation, AIModelRegistry, AIFeedback

logger = logging.getLogger("shared.ai.recommendations")


class RecommendationEngine:
    """Moteur de recommandations multi-stratégies."""

    def generate_all(self, save: bool = True) -> dict:
        """Génère toutes les recommandations (tous domaines)."""
        all_recs = []
        all_recs.extend(self._budget_recommendations())
        all_recs.extend(self._convention_recommendations())
        all_recs.extend(self._benefits_recommendations())
        all_recs.extend(self._hr_recommendations())
        all_recs.extend(self._workflow_recommendations())

        all_recs.sort(key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r["priority"], 4))

        if save:
            model = self._get_model()
            for rec in all_recs:
                AIRecommendation.objects.create(model=model, **rec)

        return {
            "generated_at": str(timezone.localdate()),
            "total": len(all_recs),
            "recommendations": all_recs,
        }

    def _budget_recommendations(self) -> list[dict]:
        """Recommandations basées sur l'état budgétaire."""
        from django.apps import apps
        try:
            Budget = apps.get_model("finance", "Budget")
            Payment = apps.get_model("finance", "Payment")
        except LookupError:
            return []

        today = timezone.localdate()
        year = today.year
        budgets = Budget.objects.filter(fiscal_year__year=year, is_deleted=False)
        if not budgets.exists():
            return []

        total_budget = budgets.aggregate(s=Sum("amount"))["s"] or 0
        paid = Payment.objects.filter(
            is_deleted=False, executed_date__year=year, status="paid",
        ).aggregate(s=Sum("amount"))["s"] or 0

        year_start = today.replace(month=1, day=1)
        progress = (today - year_start).days / 366
        consumption = paid / total_budget if total_budget else 0

        recs = []
        if consumption > progress * 1.3:
            overage = (consumption - progress) * total_budget
            recs.append({
                "domain": "finance", "priority": "high",
                "title": "Dépassement budgétaire probable",
                "detail": f"Consommation à {consumption:.0%} vs {progress:.0%} attendu. Surconsommation estimée à {overage:,.0f} DA.",
                "action_url": "/finance", "action_label": "Voir le budget",
                "confidence": 0.85,
            })
        elif consumption < progress * 0.7:
            recs.append({
                "domain": "finance", "priority": "low",
                "title": "Sous-consommation budgétaire",
                "detail": f"Consommation à {consumption:.0%} vs {progress:.0%} attendu. Vérifier les prévisions.",
                "action_url": "/finance", "action_label": "Analyser",
                "confidence": 0.7,
            })

        # Budget lines with high variance
        high_var = budgets.annotate(
            variance=Avg("variance_percent")
        ).filter(variance__gt=20)[:5]
        for b in high_var:
            recs.append({
                "domain": "finance", "priority": "medium",
                "title": f"Écart budgétaire : {b}",
                "detail": f"Écart de {b.variance_percent:.0f}% sur la ligne budgétaire.",
                "action_url": f"/finance/budgets/{b.id}",
                "action_label": "Détails",
                "confidence": 0.6,
            })
        return recs

    def _convention_recommendations(self) -> list[dict]:
        from django.apps import apps
        try:
            Convention = apps.get_model("conventions", "Convention")
        except LookupError:
            return []
        today = timezone.localdate()
        expiring = Convention.objects.alive().filter(
            end_date__gte=today, end_date__lte=today + timedelta(days=60),
        )
        recs = []
        for conv in expiring:
            delta = (conv.end_date - today).days
            recs.append({
                "domain": "conventions",
                "priority": "critical" if delta <= 7 else "high" if delta <= 30 else "medium",
                "title": f"Convention expirant dans {delta}j : {conv}",
                "detail": f"Fin le {conv.end_date}. Renouvellement à prévoir.",
                "action_url": f"/conventions/{conv.id}",
                "action_label": "Voir la convention",
                "confidence": 0.95,
            })
        return recs

    def _benefits_recommendations(self) -> list[dict]:
        from django.apps import apps
        try:
            Benefit = apps.get_model("benefits", "Benefit")
        except LookupError:
            return []
        pending = Benefit.objects.filter(
            is_deleted=False,
            workflow_state__in=["submitted", "under_review"],
        )
        count = pending.count()
        if count == 0:
            return []
        priority = "high" if count > 50 else "medium" if count > 20 else "low"
        days_old = 0
        if pending.exists():
            oldest = pending.earliest("created_at")
            days_old = (timezone.now() - oldest.created_at).days
        return [{
            "domain": "benefits", "priority": priority,
            "title": f"Backlog de {count} prestations",
            "detail": f"{count} dossiers en attente. Le plus ancien date de {days_old} jours.",
            "action_url": "/benefits?status=pending",
            "action_label": "Traiter",
            "confidence": min(0.5 + count * 0.005, 0.95),
            "source_data": {"pending_count": count, "oldest_days": days_old},
        }]

    def _hr_recommendations(self) -> list[dict]:
        from django.apps import apps
        try:
            Employee = apps.get_model("employees", "Employee")
        except LookupError:
            return []
        month_start = timezone.localdate().replace(day=1)
        new_hires = Employee.objects.alive().filter(created_at__date__gte=month_start).count()
        if new_hires < 5:
            return []
        return [{
            "domain": "hr", "priority": "low",
            "title": f"{new_hires} nouveaux employés ce mois-ci",
            "detail": "S'assurer de l'enregistrement des ayants droit et des affiliations.",
            "action_url": "/employees",
            "action_label": "Voir",
            "confidence": 0.5,
        }]

    def _workflow_recommendations(self) -> list[dict]:
        from django.apps import apps
        try:
            WorkflowLog = apps.get_model("workflow", "WorkflowLog")
        except LookupError:
            return []
        week_ago = timezone.now() - timedelta(days=7)
        bottlenecks = (
            WorkflowLog.objects.filter(timestamp__gte=week_ago)
            .values("to_state")
            .annotate(count=Count("id"))
            .order_by("-count")[:3]
        )
        recs = []
        for b in bottlenecks:
            if b["count"] > 50:
                recs.append({
                    "domain": "benefits", "priority": "medium",
                    "title": f"Goulot d'étranglement : {b['to_state']}",
                    "detail": f"{b['count']} transitions vers « {b['to_state']} » cette semaine.",
                    "confidence": 0.6,
                })
        return recs

    def collaborative_recommendations(self, user, limit: int = 5) -> list[dict]:
        """
        Recommandations basées sur l'activité d'utilisateurs similaires (collaborative).
        Simple implémentation : utilisateurs avec le même rôle qui consultent les mêmes ressources.
        """
        from .models import AIEvent
        from django.db.models import Count

        recent_events = AIEvent.objects.filter(user=user).values("target_type", "event_name").distinct()
        similar_users = AIEvent.objects.filter(
            target_type__in=[e["target_type"] for e in recent_events],
            event_name__in=[e["event_name"] for e in recent_events],
        ).exclude(user=user).values("user").annotate(sim=Count("id")).order_by("-sim")[:5]

        recs = []
        for su in similar_users:
            actions = (
                AIEvent.objects.filter(user_id=su["user"])
                .exclude(target_type__in=[e["target_type"] for e in recent_events])
                .values("target_type", "event_name")
                .annotate(count=Count("id"))
                .order_by("-count")[:3]
            )
            for a in actions:
                recs.append({
                    "domain": a["target_type"],
                    "priority": "low",
                    "title": f"Explorer {a['target_type']}",
                    "detail": f"Recommandé d'après l'activité d'utilisateurs similaires.",
                    "confidence": min(su["sim"] * 0.1, 0.8),
                })
        return recs[:limit]

    def _get_model(self):
        model, _ = AIModelRegistry.objects.get_or_create(
            name="recommendation_engine_v1",
            defaults={
                "version": "1.0.0", "task_type": "recommendation",
                "algorithm": "rule-based + collaborative", "status": "production",
            },
        )
        return model


recommendation_engine = RecommendationEngine()
