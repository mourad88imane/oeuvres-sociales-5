from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0002_alter_auditlog_action_validationtrace"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE audit_auditlog ADD COLUMN IF NOT EXISTS extra_data JSONB DEFAULT '{}'::jsonb NOT NULL;",
                    reverse_sql="ALTER TABLE audit_auditlog DROP COLUMN extra_data;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE audit_auditlog ADD COLUMN IF NOT EXISTS request_id VARCHAR(100) NOT NULL DEFAULT '';",
                    reverse_sql="ALTER TABLE audit_auditlog DROP COLUMN request_id;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE audit_auditlog ADD COLUMN IF NOT EXISTS endpoint VARCHAR(500) NOT NULL DEFAULT '';",
                    reverse_sql="ALTER TABLE audit_auditlog DROP COLUMN endpoint;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE audit_auditlog ADD COLUMN IF NOT EXISTS http_method VARCHAR(10) NOT NULL DEFAULT '';",
                    reverse_sql="ALTER TABLE audit_auditlog DROP COLUMN http_method;",
                ),
            ],
            state_operations=[],
        ),
    ]
