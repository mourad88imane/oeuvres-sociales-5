"""
============================================================
AI ASSISTANT — Assistant IA conversationnel (intent-based)
============================================================
Fonctionnement :
  1. Intent matching (reconnaissance de l'intention)
  2. Entity extraction (extraction des paramètres)
  3. Data retrieval (récupération des données)
  4. Response generation (template + data)

Pas de LLM externe — règles et templates pour MVP.
Architecture prête pour RAG (Retrieval Augmented Generation).
"""

import logging
import re
from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger("shared.ai.assistant")


class Intent:
    """Intentions reconnues par l'assistant."""

    DASHBOARD_SUMMARY = "dashboard_summary"
    KPI_QUERY = "kpi_query"
    BUDGET_STATUS = "budget_status"
    BENEFITS_STATUS = "benefits_status"
    CONVENTION_EXPIRY = "convention_expiry"
    ANOMALIES = "anomalies"
    RECOMMENDATIONS = "recommendations"
    EMPLOYEE_COUNT = "employee_count"
    USER_HELP = "user_help"
    FORECAST = "forecast"
    UNKNOWN = "unknown"


class AIAssistant:
    """Assistant IA — répond aux questions en langage naturel."""

    # Patterns d'intention (regex simples)
    INTENT_PATTERNS: list[tuple[str, str]] = [
        (r"(bonjour|salut|coucou|hello|hi)", "greeting"),
        (
            r"(récapitulatif|synthèse|dashboard|tableau de bord|vue d.ensemble|summary)",
            Intent.DASHBOARD_SUMMARY,
        ),
        (r"(kpi|indicateur|performance|métrique)", Intent.KPI_QUERY),
        (r"(budget|dépense|consommation budgétaire|finance)", Intent.BUDGET_STATUS),
        (r"(prestation|demande|bénéfice|prestation sociale|dossier)", Intent.BENEFITS_STATUS),
        (
            r"(convention|expir|renouvellement|partenaire|convention arriv)",
            Intent.CONVENTION_EXPIRY,
        ),
        (r"(anomalie|détection|alerte|suspect|anormal)", Intent.ANOMALIES),
        (r"(recommendation|recommandation|conseil|suggestion|proposition)", Intent.RECOMMENDATIONS),
        (r"(employé|salarié|effectif|combien.*employé)", Intent.EMPLOYEE_COUNT),
        (r"(prévision|prédiction|tendance|évolution|projection|estimation)", Intent.FORECAST),
        (r"(aide|help|que fais|commandes|possible)", Intent.USER_HELP),
    ]

    def __init__(self):
        self.context = {}

    def process(self, query: str, user=None) -> dict:
        """Traite une requête et retourne une réponse structurée."""
        intent = self._detect_intent(query)
        entities = self._extract_entities(query)
        response = self._handle_intent(intent, entities, user)
        return {
            "query": query,
            "intent": intent,
            "entities": entities,
            "response": response,
        }

    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower().strip()
        for pattern, intent in self.INTENT_PATTERNS:
            if re.search(pattern, query_lower):
                return intent
        return Intent.UNKNOWN

    def _extract_entities(self, query: str) -> dict:
        """Extraction d'entités simples (dates, montants, etc.)."""
        entities = {}
        # Dates relatives
        if re.search(r"(aujourd'hui|aujourd hui)", query):
            entities["date"] = str(timezone.localdate())
        if re.search(r"(cette semaine|7 jours|7j)", query):
            entities["period_days"] = 7
        if re.search(r"(ce mois|30 jours|30j)", query):
            entities["period_days"] = 30
        if re.search(r"(cette année|365 jours|an)", query):
            entities["period_days"] = 365

        # KPI codes
        kpi_match = re.search(r"kpi[:_]\s*(\w+)", query)
        if kpi_match:
            entities["kpi_code"] = kpi_match.group(1)

        return entities

    def _handle_intent(self, intent: str, entities: dict, user=None) -> dict:
        handlers = {
            "greeting": self._greeting,
            Intent.DASHBOARD_SUMMARY: self._dashboard_summary,
            Intent.KPI_QUERY: self._kpi_query,
            Intent.BUDGET_STATUS: self._budget_status,
            Intent.BENEFITS_STATUS: self._benefits_status,
            Intent.CONVENTION_EXPIRY: self._convention_expiry,
            Intent.ANOMALIES: self._anomalies,
            Intent.RECOMMENDATIONS: self._recommendations,
            Intent.EMPLOYEE_COUNT: self._employee_count,
            Intent.FORECAST: self._forecast,
            Intent.USER_HELP: self._user_help,
            Intent.UNKNOWN: self._unknown,
        }
        handler = handlers.get(intent, self._unknown)
        return handler(entities, user)

    def _greeting(self, entities: dict, user=None) -> dict:
        name = user.get_full_name() if user and hasattr(user, "get_full_name") else "Utilisateur"
        return {
            "text": f"Bonjour {name} ! Je suis l'assistant IA des Œuvres Sociales. "
            "Je peux vous aider avec le tableau de bord, les KPI, le budget, "
            "les prestations, les conventions, et plus encore. Tapez « aide » "
            "pour voir ce que je sais faire.",
            "type": "text",
            "suggestions": [
                "Récapitulatif du tableau de bord",
                "État du budget",
                "Prestations en attente",
                "Conventions arrivant à expiration",
            ],
        }

    def _dashboard_summary(self, entities: dict, user=None) -> dict:
        from django.apps import apps

        try:
            Employee = apps.get_model("employees", "Employee")
            Benefit = apps.get_model("benefits", "Benefit")
            Convention = apps.get_model("conventions", "Convention")
        except LookupError:
            return {"text": "Je n'arrive pas à accéder aux données.", "type": "text"}

        today = timezone.localdate()
        employees = Employee.objects.alive().count()
        pending = (
            Benefit.objects.alive().filter(workflow_state__in=["submitted", "under_review"]).count()
        )
        expiring = (
            Convention.objects.alive()
            .filter(end_date__gte=today, end_date__lte=today + timedelta(days=30))
            .count()
        )

        return {
            "text": (
                f"📊 **Récapitulatif**\n\n"
                f"• {employees} employés actifs\n"
                f"• {pending} prestations en attente\n"
                f"• {expiring} conventions expirent dans 30 jours\n\n"
                f"Voulez-vous plus de détails sur un domaine spécifique ?"
            ),
            "type": "rich",
            "data": {
                "employees": employees,
                "pending_benefits": pending,
                "expiring_conventions": expiring,
            },
        }

    def _kpi_query(self, entities: dict, user=None) -> dict:
        return {
            "text": "Je peux vous montrer les indicateurs KPI. Pour le moment, consultez l'onglet Analytics.",
            "type": "text",
        }

    def _budget_status(self, entities: dict, user=None) -> dict:
        from django.apps import apps

        try:
            Budget = apps.get_model("finance", "Budget")
            Payment = apps.get_model("finance", "Payment")
        except LookupError:
            return {"text": "Module finance non disponible.", "type": "text"}

        year = timezone.localdate().year
        total = (
            Budget.objects.filter(fiscal_year__year=year, is_deleted=False).aggregate(
                s=Sum("allocated_amount")
            )["s"]
            or 0
        )
        paid = (
            Payment.objects.filter(
                is_deleted=False, executed_date__year=year, status="paid"
            ).aggregate(s=Sum("amount"))["s"]
            or 0
        )
        pct = (paid / total * 100) if total else 0

        return {
            "text": (
                f"💰 **Budget {year}**\n\n"
                f"Budget total : {total:,.0f} DA\n"
                f"Dépensé : {paid:,.0f} DA ({pct:.1f}%)\n"
                f"Reste : {total - paid:,.0f} DA\n"
                f"{'⚠️' if pct > 80 else '✅'} Consommation {'élevée' if pct > 80 else 'normale'}."
            ),
            "type": "rich",
            "data": {"total_budget": total, "spent": paid, "percentage": round(pct, 1)},
        }

    def _benefits_status(self, entities: dict, user=None) -> dict:
        from django.apps import apps

        try:
            Benefit = apps.get_model("benefits", "Benefit")
        except LookupError:
            return {"text": "Module prestations non disponible.", "type": "text"}

        total = Benefit.objects.alive().count()
        pending = (
            Benefit.objects.alive().filter(workflow_state__in=["submitted", "under_review"]).count()
        )
        by_status = list(
            Benefit.objects.alive()
            .values("workflow_state")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "text": (
                f"📋 **Prestations**\n\n"
                f"Total : {total}\n"
                f"En attente : {pending}\n\n"
                f"Répartition :\n"
                + "\n".join(f"  • {s['workflow_state']}: {s['count']}" for s in by_status[:5])
            ),
            "type": "rich",
            "data": {"total": total, "pending": pending, "by_status": by_status},
        }

    def _convention_expiry(self, entities: dict, user=None) -> dict:
        from django.apps import apps

        try:
            Convention = apps.get_model("conventions", "Convention")
        except LookupError:
            return {"text": "Module conventions non disponible.", "type": "text"}

        today = timezone.localdate()
        expiring = Convention.objects.alive().filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30),
        )
        count = expiring.count()
        if count == 0:
            return {
                "text": "✅ Aucune convention n'arrive à expiration dans les 30 prochains jours.",
                "type": "text",
            }

        details = "\n".join(f"  • {c} — expire le {c.end_date}" for c in expiring[:5])
        return {
            "text": f"⚠️ **{count} convention(s) expirent dans 30 jours**\n\n{details}",
            "type": "rich",
        }

    def _anomalies(self, entities: dict, user=None) -> dict:
        from .models import AIAnomaly

        recent = AIAnomaly.objects.filter(status="new").order_by("-severity", "-created_at")[:5]
        if not recent.exists():
            return {"text": "✅ Aucune anomalie détectée récemment.", "type": "text"}
        details = "\n".join(
            f"  • [{a.get_severity_display()}] {a.explanation or a.metric_name}" for a in recent
        )
        return {"text": f"🔍 **{recent.count()} anomalies en cours**\n\n{details}", "type": "rich"}

    def _recommendations(self, entities: dict, user=None) -> dict:
        from .models import AIRecommendation

        recs = AIRecommendation.objects.filter(is_active=True, feedback="pending").order_by(
            "priority", "-created_at"
        )[:5]
        if not recs.exists():
            return {"text": "Aucune recommandation active pour le moment.", "type": "text"}
        details = "\n".join(f"  • [{r.get_priority_display()}] {r.title}" for r in recs)
        return {"text": f"💡 **Recommandations**\n\n{details}", "type": "rich"}

    def _employee_count(self, entities: dict, user=None) -> dict:
        from django.apps import apps

        try:
            Employee = apps.get_model("employees", "Employee")
        except LookupError:
            return {"text": "Module employés non disponible.", "type": "text"}
        total = Employee.objects.alive().count()
        active = Employee.objects.alive().filter(status="active").count()
        by_dept = list(
            Employee.objects.alive()
            .values("department__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        return {
            "text": (
                f"👥 **Effectifs**\n\n"
                f"Total : {total}\n"
                f"Actifs : {active}\n\n"
                f"Top départements :\n"
                + "\n".join(
                    f"  • {d['department__name'] or 'Sans département'}: {d['count']}"
                    for d in by_dept
                )
            ),
            "type": "rich",
        }

    def _forecast(self, entities: dict, user=None) -> dict:
        return {
            "text": (
                "📈 **Prévisions disponibles**\n\n"
                "• Tendance des prestations (3 mois)\n"
                "• Consommation budgétaire (fin d'année)\n"
                "• Simulation Monte Carlo\n\n"
                "Consultez l'onglet Analytics pour les graphiques détaillés."
            ),
            "type": "text",
        }

    def _user_help(self, entities: dict, user=None) -> dict:
        return {
            "text": (
                "🤖 **Commandes disponibles**\n\n"
                "• « Récapitulatif » — Vue d'ensemble\n"
                "• « Budget/Finances » — État budgétaire\n"
                "• « Prestations » — Demandes en cours\n"
                "• « Conventions » — Expirations\n"
                "• « Anomalies » — Alertes récentes\n"
                "• « Recommandations » — Suggestions\n"
                "• « Employés » — Effectifs\n"
                "• « Prévisions » — Tendances\n\n"
                "Posez une question en langage naturel !"
            ),
            "type": "text",
        }

    def _unknown(self, entities: dict, user=None) -> dict:
        return {
            "text": (
                "Je n'ai pas compris votre demande. "
                "Essayez des mots-clés comme : budget, prestations, conventions, "
                "employés, récapitulatif, anomalies, ou tapez « aide »."
            ),
            "type": "text",
        }


ai_assistant = AIAssistant()
