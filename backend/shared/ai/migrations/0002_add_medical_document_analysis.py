# Generated manually

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MedicalDocumentAnalysis",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=255)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("prescription", "Ordonnance"),
                            ("report", "Rapport médical"),
                            ("imaging", "Imagerie"),
                            ("lab_result", "Résultat d'analyse"),
                            ("invoice", "Facture"),
                            ("id_document", "Pièce d'identité"),
                            ("other", "Autre"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
                ("extracted_text", models.TextField(blank=True)),
                ("ocr_confidence", models.FloatField(blank=True, null=True)),
                ("medical_keywords", models.JSONField(blank=True, default=list)),
                ("diagnosis_mentions", models.JSONField(blank=True, default=list)),
                ("medication_mentions", models.JSONField(blank=True, default=list)),
                ("summary", models.TextField(blank=True)),
                ("language", models.CharField(blank=True, default="fr", max_length=10)),
                ("file_name", models.CharField(blank=True, max_length=500)),
                ("file_size_bytes", models.PositiveIntegerField(blank=True, null=True)),
                ("file_type", models.CharField(blank=True, max_length=50)),
                ("page_count", models.PositiveIntegerField(blank=True, null=True)),
                ("analysis_duration_ms", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("completed", "Terminé"),
                            ("failed", "Échec"),
                        ],
                        default="completed",
                        max_length=15,
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "analyzed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("related_entity_type", models.CharField(blank=True, max_length=50)),
                ("related_entity_id", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Analyse document IA",
                "verbose_name_plural": "Analyses documents IA",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["category"], name="ai_medicald_categor_f8a1f2_idx"),
                    models.Index(fields=["status"], name="ai_medicald_status_e3ad2b_idx"),
                ],
            },
        ),
    ]
