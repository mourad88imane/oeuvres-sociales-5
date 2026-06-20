# Generated manually — replaces hardcoded MedicalCoverageRequest FK with GenericForeignKey

import django.db.models.deletion
from django.db import migrations, models


def backfill_approval_history(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ApprovalHistory = apps.get_model("administration", "ApprovalHistory")
    try:
        ct = ContentType.objects.get(app_label="medical_coverage", model="medicalcoveragerequest")
    except ContentType.DoesNotExist:
        ct = None
    if ct is None:
        return
    manager = getattr(ApprovalHistory, "objects", None) or getattr(ApprovalHistory, "_base_manager", None)
    if manager is not None:
        manager.filter(request__isnull=False).update(
            content_type=ct,
            object_id=models.F("request_id"),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0006_approvalhistory_tenant_approvalmatrix_tenant_and_more"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="approvalhistory",
            name="content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
                verbose_name="Type de contenu",
            ),
        ),
        migrations.AddField(
            model_name="historicalapprovalhistory",
            name="content_type",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="contenttypes.contenttype",
                verbose_name="Type de contenu",
            ),
        ),
        migrations.AddField(
            model_name="approvalhistory",
            name="object_id",
            field=models.UUIDField(
                blank=True,
                null=True,
                verbose_name="ID de l'objet",
            ),
        ),
        migrations.AddField(
            model_name="historicalapprovalhistory",
            name="object_id",
            field=models.UUIDField(
                blank=True,
                null=True,
                verbose_name="ID de l'objet",
            ),
        ),
        migrations.RunPython(backfill_approval_history, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="approvalhistory",
            name="request",
        ),
        migrations.RemoveField(
            model_name="historicalapprovalhistory",
            name="request",
        ),
        migrations.AddIndex(
            model_name="approvalhistory",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="approval_history_gfk_idx",
            ),
        ),
    ]
