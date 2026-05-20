import django.db.models.deletion
import django.utils.timezone
import simple_history.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalUser",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                (
                    "email",
                    models.EmailField(db_index=True, max_length=254, verbose_name="Adresse email"),
                ),
                ("first_name", models.CharField(max_length=150, verbose_name="Prénom")),
                ("last_name", models.CharField(max_length=150, verbose_name="Nom")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Téléphone")),
                (
                    "avatar",
                    models.TextField(blank=True, max_length=100, null=True, verbose_name="Avatar"),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Administrateur"),
                            ("gestionnaire", "Gestionnaire RH"),
                            ("comptable", "Comptable"),
                            ("consultant", "Consultant"),
                        ],
                        default="consultant",
                        max_length=20,
                        verbose_name="Rôle",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Actif")),
                ("is_staff", models.BooleanField(default=False, verbose_name="Staff Django")),
                (
                    "must_change_password",
                    models.BooleanField(
                        default=True,
                        help_text="Forcé après la première connexion ou reset admin",
                        verbose_name="Doit changer le mot de passe",
                    ),
                ),
                (
                    "last_login_ip",
                    models.GenericIPAddressField(
                        blank=True, null=True, verbose_name="Dernière IP de connexion"
                    ),
                ),
                (
                    "failed_login_count",
                    models.PositiveIntegerField(default=0, verbose_name="Tentatives échouées"),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Date d'inscription"
                    ),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("updated_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "preferences",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Stockage JSON pour préférences UI et paramètres personnalisés",
                        verbose_name="Préférences utilisateur",
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.TextField(null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")], max_length=1
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Utilisateur",
                "verbose_name_plural": "historical Utilisateurs",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
