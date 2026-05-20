"""
============================================================
BEHAVIOR ANALYSIS — Segmentation, patterns, profils de risque
============================================================
Analyse des comportements utilisateurs :
  - Segmentation par activité
  - Détection de patterns inhabituels
  - Profils de risque (fraude, erreur)
  - Métriques d'engagement
"""
import logging
from collections import Counter
from datetime import date, timedelta
from statistics import mean, stdev
from typing import Optional

from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import AIEvent, AIAnomaly, AIScore, AIModelRegistry

logger = logging.getLogger("shared.ai.behavior")


class BehaviorAnalyzer:
    """Analyse comportementale des utilisateurs."""

    def analyze_user_activity(self, user, days: int = 30) -> dict:
        """Analyse complète de l'activité d'un utilisateur."""
        since = timezone.now() - timedelta(days=days)
        events = AIEvent.objects.filter(user=user, timestamp__gte=since)
        total = events.count()
        if total == 0:
            return {"user": str(user), "period_days": days, "total_events": 0}

        by_category = list(
            events.values("event_category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_hour = list(
            events.extra({"hour": "EXTRACT(hour FROM timestamp)"})
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        top_actions = list(
            events.values("event_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        sessions = events.values("session_id").distinct().count()
        avg_duration = events.aggregate(avg=Avg("duration_ms"))["avg"] or 0

        return {
            "user": str(user),
            "period_days": days,
            "total_events": total,
            "events_per_day": round(total / max(days, 1), 1),
            "sessions": sessions,
            "avg_duration_ms": round(avg_duration, 1),
            "by_category": by_category,
            "by_hour": by_hour,
            "top_actions": top_actions,
            "active_days": events.dates("timestamp", "day").count(),
        }

    def segment_users(self, days: int = 30) -> list[dict]:
        """Segmente les utilisateurs par niveau d'activité."""
        since = timezone.now() - timedelta(days=days)
        user_activity = (
            AIEvent.objects.filter(timestamp__gte=since)
            .values("user", "user_email")
            .annotate(
                total=Count("id"),
                unique_actions=Count("event_name", distinct=True),
                total_duration=Avg("duration_ms"),
            )
            .order_by("-total")
        )
        segments = {"power": [], "regular": [], "occasional": [], "inactive": []}
        for ua in user_activity:
            if ua["total"] > 100:
                segments["power"].append(ua)
            elif ua["total"] > 30:
                segments["regular"].append(ua)
            elif ua["total"] > 5:
                segments["occasional"].append(ua)
            else:
                segments["inactive"].append(ua)

        return [
            {"segment": "Power users", "count": len(segments["power"]), "description": "> 100 événements/30j"},
            {"segment": "Utilisateurs réguliers", "count": len(segments["regular"]), "description": "30-100 événements/30j"},
            {"segment": "Utilisateurs occasionnels", "count": len(segments["occasional"]), "description": "5-30 événements/30j"},
            {"segment": "Utilisateurs inactifs", "count": len(segments["inactive"]), "description": "< 5 événements/30j"},
        ]

    def detect_suspicious_behavior(self, days: int = 7) -> list[dict]:
        """Détecte les comportements suspects (tentatives d'accès, patterns inhabituels)."""
        since = timezone.now() - timedelta(days=days)
        alerts = []

        # 1. Multiple failed login patterns
        failed_logins = (
            AIEvent.objects.filter(event_name="login_failed", timestamp__gte=since)
            .values("user", "ip_address")
            .annotate(count=Count("id"))
            .filter(count__gte=5)
        )
        for fl in failed_logins:
            alerts.append({
                "type": "multiple_failed_logins",
                "severity": "high",
                "user_id": str(fl["user"]),
                "ip": fl["ip_address"],
                "count": fl["count"],
                "detail": f"{fl['count']} échecs de connexion depuis {fl['ip_address']}",
            })

        # 2. High volume of exports
        high_exports = (
            AIEvent.objects.filter(event_category="export", timestamp__gte=since)
            .values("user")
            .annotate(count=Count("id"))
            .filter(count__gte=20)
        )
        for he in high_exports:
            alerts.append({
                "type": "high_export_volume",
                "severity": "medium",
                "user_id": str(he["user"]),
                "count": he["count"],
                "detail": f"{he['count']} exports en {days} jours",
            })

        # 3. Unusual access times (e.g., 2am-5am)
        unusual = (
            AIEvent.objects.filter(timestamp__gte=since)
            .extra({"hour": "EXTRACT(hour FROM timestamp)"})
            .filter(hour__gte=0, hour__lte=5)
            .values("user")
            .annotate(count=Count("id"))
            .filter(count__gte=10)
        )
        for ua in unusual:
            alerts.append({
                "type": "unusual_access_hours",
                "severity": "low",
                "user_id": str(ua["user"]),
                "count": ua["count"],
                "detail": f"{ua['count']} accès entre minuit et 5h du matin",
            })

        return alerts

    def user_risk_profile(self, user) -> dict:
        """Calcule le profil de risque d'un utilisateur basé sur son historique."""
        from django.apps import apps
        User = apps.get_model("users", "User")

        events_30d = AIEvent.objects.filter(user=user, timestamp__gte=timezone.now() - timedelta(days=30)).count()
        anomalies = AIAnomaly.objects.filter(target_type="User", target_id=str(user.pk)).count()
        failed_logins = AIEvent.objects.filter(user=user, event_name="login_failed", timestamp__gte=timezone.now() - timedelta(days=7)).count()

        risk = 0
        risk += min(events_30d * 0.5, 20)
        risk += min(anomalies * 15, 30)
        risk += min(failed_logins * 10, 30)

        factors = []
        if events_30d > 200:
            factors.append({"name": "activité_élevée", "impact": "+20", "detail": f"{events_30d} événements en 30j"})
        if anomalies > 0:
            factors.append({"name": "anomalies_passées", "impact": f"+{anomalies * 15}", "detail": f"{anomalies} anomalies"})
        if failed_logins > 3:
            factors.append({"name": "échecs_connexion", "impact": f"+{failed_logins * 10}", "detail": f"{failed_logins} échecs en 7j"})

        return {
            "user_id": str(user.pk),
            "risk_score": round(min(risk, 100), 1),
            "risk_level": "low" if risk < 30 else "medium" if risk < 60 else "high",
            "factors": factors,
            "events_30d": events_30d,
            "anomalies": anomalies,
            "failed_logins_7d": failed_logins,
        }


behavior_analyzer = BehaviorAnalyzer()
