from django.db import migrations

APP_MODELS = [
    ("administration", "ApprovalHistory"),
    ("administration", "ApprovalMatrix"),
    ("administration", "Permission"),
    ("administration", "Role"),
    ("administration", "RolePermission"),
    ("administration", "SystemParameter"),
    ("administration", "UserRoleAssignment"),
    ("administration", "WorkflowPermission"),
    ("beneficiaries", "Beneficiary"),
    ("benefits", "Benefit"),
    ("benefits", "BenefitAttachment"),
    ("benefits", "BenefitComment"),
    ("benefits", "BenefitType"),
    ("conventions", "Convention"),
    ("conventions", "ConventionAlert"),
    ("conventions", "ConventionDocument"),
    ("conventions", "Partner"),
    ("departments", "Department"),
    ("employees", "Employee"),
    ("finance", "Budget"),
    ("finance", "FinancialAlert"),
    ("finance", "FinancialEntry"),
    ("finance", "FiscalYear"),
    ("finance", "Payment"),
    ("finance", "PaymentBatch"),
    ("loans", "Loan"),
    ("loans", "LoanAttachment"),
    ("loans", "LoanComment"),
    ("medical_coverage", "MedicalCoverageRequest"),
    ("medical_coverage", "MedicalCoverageType"),
    ("medical_coverage", "MedicalCoverageVoucher"),
    ("medical_coverage", "MedicalProvider"),
    ("notifications", "Notification"),
    ("notifications", "NotificationPreference"),
    ("reporting", "DashboardWidget"),
    ("reporting", "DataExport"),
    ("reporting", "KpiDefinition"),
    ("reporting", "KpiSnapshot"),
    ("reporting", "ReportDefinition"),
    ("reporting", "ReportSchedule"),
]


def assign_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenant", "Tenant")
    default = Tenant.objects.filter(slug="default").first()
    if default is None:
        return
    for app_label, model_name in APP_MODELS:
        Model = apps.get_model(app_label, model_name)
        if Model is None:
            continue
        manager = getattr(Model, "objects", None) or getattr(Model, "_base_manager", None)
        if manager is None:
            continue
        try:
            manager.filter(tenant__isnull=True).update(tenant=default)
        except Exception:
            pass


def reverse_assign(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0002_seed_default_tenant"),
        ("administration", "0006_approvalhistory_tenant_approvalmatrix_tenant_and_more"),
        ("beneficiaries", "0005_beneficiary_tenant_historicalbeneficiary_tenant"),
        ("benefits", "0002_alter_benefit_managers_and_more"),
        ("conventions", "0004_convention_tenant_conventionalert_tenant_and_more"),
        ("departments", "0003_alter_department_managers_department_tenant_and_more"),
        ("employees", "0003_employee_tenant_historicalemployee_tenant"),
        ("finance", "0002_alter_budget_managers_alter_financialalert_managers_and_more"),
        ("loans", "0002_historicalloan_tenant_and_more"),
        ("medical_coverage", "0005_historicalmedicalcoveragerequest_tenant_and_more"),
        ("notifications", "0002_alter_notification_managers_and_more"),
        ("reporting", "0003_alter_dashboardwidget_managers_and_more"),
    ]

    operations = [
        migrations.RunPython(assign_default_tenant, reverse_assign),
    ]
