from django.db import migrations

from core.models import SoftDeleteManager


def seed_default_parameters(apps, schema_editor):
    SystemParameter = apps.get_model("administration", "SystemParameter")
    defaults = [
        {
            "key": "coverage_restriction_period_months",
            "value": "3",
            "description": "Période de restriction (en mois) pour l'auto-validation des demandes de couverture médicale. 0 requête dans cette période → validation automatique.",
        },
        {
            "key": "max_coverage_amount_per_request",
            "value": "500000",
            "description": "Montant maximum (DZD) par demande de couverture médicale.",
        },
        {
            "key": "max_annual_coverage_requests",
            "value": "4",
            "description": "Nombre maximum de demandes de couverture par employé par année civile.",
        },
        {
            "key": "coverage_approval_requires_committee",
            "value": "false",
            "description": "Si 'true', la validation nécessite un vote de commission. Si 'false', le chef de service peut valider seul.",
        },
        {
            "key": "director_escalation_threshold_amount",
            "value": "300000",
            "description": "Montant (DZD) au-dessus duquel la demande est automatiquement escaladée au directeur.",
        },
    ]
    for param in defaults:
        SystemParameter.all_objects.get_or_create(
            key=param["key"],
            defaults=param,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_parameters, migrations.RunPython.noop),
    ]
