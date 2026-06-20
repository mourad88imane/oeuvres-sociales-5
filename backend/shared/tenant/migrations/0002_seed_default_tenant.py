from django.db import migrations


def seed_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenant", "Tenant")
    if not Tenant.objects.filter(slug="default").exists():
        Tenant.objects.create(
            slug="default",
            name="Organisme par défaut",
            is_active=True,
            max_users=1000,
            config={
                "language": "fr",
                "timezone": "Africa/Algiers",
            },
            features={
                "workflow_designer": True,
                "multi_language": True,
                "ai_assistant": True,
            },
        )


def reverse_seed(apps, schema_editor):
    Tenant = apps.get_model("tenant", "Tenant")
    Tenant.objects.filter(slug="default").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_tenant, reverse_seed),
    ]
