from django.db import migrations


def assign_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenant", "Tenant")
    User = apps.get_model("users", "User")
    HistoricalUser = apps.get_model("users", "HistoricalUser")

    default = Tenant.objects.filter(slug="default").first()
    if default is None:
        return

    User.objects.filter(tenant__isnull=True).update(tenant=default)
    HistoricalUser.objects.filter(tenant__isnull=True).update(tenant=default)


def reverse_assign(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_tenant"),
    ]

    operations = [
        migrations.RunPython(assign_default_tenant, reverse_assign),
    ]
