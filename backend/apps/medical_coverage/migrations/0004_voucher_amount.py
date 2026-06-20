from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("medical_coverage", "0003_add_new_approval_states"),
    ]

    operations = [
        migrations.AddField(
            model_name="medicalcoveragevoucher",
            name="amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Montant estimé de la prise en charge",
                max_digits=12,
                null=True,
                verbose_name="Montant",
            ),
        ),
        migrations.AddField(
            model_name="medicalcoveragevoucher",
            name="approved_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name="Montant approuvé",
            ),
        ),
        migrations.AddField(
            model_name="historicalmedicalcoveragevoucher",
            name="amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Montant estimé de la prise en charge",
                max_digits=12,
                null=True,
                verbose_name="Montant",
            ),
        ),
        migrations.AddField(
            model_name="historicalmedicalcoveragevoucher",
            name="approved_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name="Montant approuvé",
            ),
        ),
    ]
