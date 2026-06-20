import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[str] = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, verbose_name="Nom")),
                ("slug", models.SlugField(max_length=100, unique=True, verbose_name="Slug")),
                ("domain", models.CharField(blank=True, help_text="Domaine personnalisé (optionnel)", max_length=200, verbose_name="Domaine")),
                ("logo", models.ImageField(blank=True, null=True, upload_to="tenants/", verbose_name="Logo")),
                ("is_active", models.BooleanField(default=True, verbose_name="Actif")),
                ("max_users", models.PositiveIntegerField(default=100, verbose_name="Nombre max d'utilisateurs")),
                ("config", models.JSONField(blank=True, default=dict, verbose_name="Configuration")),
                ("features", models.JSONField(blank=True, default=dict, help_text="Feature flags au format JSON", verbose_name="Fonctionnalités")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Tenant",
                "verbose_name_plural": "Tenants",
                "ordering": ["name"],
            },
        ),
    ]
