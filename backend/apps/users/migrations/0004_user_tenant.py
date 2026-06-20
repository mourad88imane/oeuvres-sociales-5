from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0002_seed_default_tenant"),
        ("users", "0003_alter_historicaluser_role_alter_user_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                to="tenant.tenant",
                verbose_name="Organisme",
                help_text="Organisme de rattachement (multi-tenant)",
            ),
        ),
        migrations.AddField(
            model_name="historicaluser",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=models.SET_NULL,
                to="tenant.tenant",
                verbose_name="Organisme",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["tenant"], name="users_user_tenant_8c1ea0_idx"),
        ),
    ]
