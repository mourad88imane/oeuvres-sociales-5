from django.db import migrations


SEED_KPIS = [
    {"code": "total_employees", "name": "Effectif total", "category": "hr", "unit": "employés", "display_order": 10},
    {"code": "active_employees", "name": "Employés actifs", "category": "hr", "unit": "employés", "display_order": 20},
    {"code": "active_rate", "name": "Taux d'activité", "category": "hr", "unit": "%", "display_order": 30},
    {"code": "total_beneficiaries", "name": "Ayants droit", "category": "hr", "unit": "bénéficiaires", "display_order": 40},
    {"code": "beneficiaries_per_employee", "name": "Ratio ayants droit/employé", "category": "hr", "unit": "ratio", "display_order": 50},
    {"code": "total_benefits", "name": "Total prestations", "category": "benefits", "unit": "prestations", "display_order": 60},
    {"code": "total_benefits_amount", "name": "Montant total prestations", "category": "benefits", "unit": "DZD", "display_order": 70},
    {"code": "avg_benefit_amount", "name": "Montant moyen par prestation", "category": "benefits", "unit": "DZD", "display_order": 80},
    {"code": "month_benefits_amount", "name": "Prestations du mois", "category": "benefits", "unit": "DZD", "display_order": 90},
    {"code": "total_conventions", "name": "Total conventions", "category": "conventions", "unit": "conventions", "display_order": 100},
    {"code": "active_conventions", "name": "Conventions actives", "category": "conventions", "unit": "conventions", "display_order": 110},
    {"code": "expired_conventions", "name": "Conventions expirées", "category": "conventions", "unit": "conventions", "display_order": 120},
    {"code": "convention_active_rate", "name": "Taux de conventions actives", "category": "conventions", "unit": "%", "display_order": 130},
    {"code": "total_budget", "name": "Budget total", "category": "finance", "unit": "DZD", "display_order": 140},
    {"code": "total_paid", "name": "Total payé", "category": "finance", "unit": "DZD", "display_order": 150},
    {"code": "year_paid", "name": "Payé cette année", "category": "finance", "unit": "DZD", "display_order": 160},
    {"code": "consumption_rate", "name": "Taux de consommation", "category": "finance", "unit": "%", "target_value": 85, "display_order": 170},
    {"code": "pending_payments", "name": "Paiements en attente", "category": "finance", "unit": "paiements", "display_order": 180},
    {"code": "avg_payment_amount", "name": "Montant moyen par paiement", "category": "finance", "unit": "DZD", "display_order": 190},
]

SEED_REPORTS = [
    {
        "code": "report_employees",
        "title": "Liste des employés",
        "category": "employees",
        "description": "Export complet de la base employés avec matricule, département, statut.",
        "is_system": True,
    },
    {
        "code": "report_benefits",
        "title": "Prestations par période",
        "category": "benefits",
        "description": "Liste des prestations avec filtres par date, type et statut.",
        "is_system": True,
    },
    {
        "code": "report_finance_payments",
        "title": "Paiements effectués",
        "category": "finance",
        "description": "Export des paiements avec détails bancaires.",
        "is_system": True,
    },
    {
        "code": "report_conventions",
        "title": "Conventions en cours",
        "category": "conventions",
        "description": "Liste des conventions avec partenaires, montants et échéances.",
        "is_system": True,
    },
    {
        "code": "report_kpi_summary",
        "title": "Synthèse des KPI",
        "category": "kpi",
        "description": "Tous les indicateurs clés calculés avec tendances.",
        "is_system": True,
    },
    {
        "code": "report_finance_budget",
        "title": "Consommation budgétaire",
        "category": "finance",
        "description": "Analyse détaillée de la consommation budgétaire par poste.",
        "is_system": True,
    },
]


def seed_data(apps, schema_editor):
    KpiDefinition = apps.get_model("reporting", "KpiDefinition")
    ReportDefinition = apps.get_model("reporting", "ReportDefinition")

    for kpi_data in SEED_KPIS:
        KpiDefinition.objects.get_or_create(
            code=kpi_data["code"],
            defaults={**kpi_data, "formula": kpi_data.get("code", "")},
        )

    for report_data in SEED_REPORTS:
        ReportDefinition.objects.get_or_create(
            code=report_data["code"],
            defaults=report_data,
        )


def reverse_seed(apps, schema_editor):
    KpiDefinition = apps.get_model("reporting", "KpiDefinition")
    ReportDefinition = apps.get_model("reporting", "ReportDefinition")
    KpiDefinition.objects.filter(code__in=[k["code"] for k in SEED_KPIS]).delete()
    ReportDefinition.objects.filter(code__in=[r["code"] for r in SEED_REPORTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("reporting", "0001_initial_reporting"),
    ]
    operations = [
        migrations.RunPython(seed_data, reverse_seed),
    ]
