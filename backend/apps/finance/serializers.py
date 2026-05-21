"""Finance serializers."""

from rest_framework import serializers

from core.serializers import BaseModelSerializer

from .models import Budget, FinancialAlert, FinancialEntry, FiscalYear, Payment, PaymentBatch


# ── FiscalYear ────────────────────────────────────────────
class FiscalYearListSerializer(serializers.ModelSerializer):
    consumption_rate = serializers.ReadOnlyField()
    available_budget = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = FiscalYear
        fields = [
            "id",
            "year",
            "label",
            "start_date",
            "end_date",
            "status",
            "status_display",
            "total_budget",
            "total_paid",
            "total_committed",
            "consumption_rate",
            "available_budget",
            "is_active",
        ]


class FiscalYearSerializer(BaseModelSerializer):
    consumption_rate = serializers.ReadOnlyField()
    available_budget = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = FiscalYear
        fields = [
            "id",
            "year",
            "label",
            "start_date",
            "end_date",
            "status",
            "status_display",
            "total_budget",
            "total_paid",
            "total_committed",
            "consumption_rate",
            "available_budget",
            "is_active",
            "notes",
            "closed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_paid",
            "total_committed",
            "closed_at",
            "created_at",
            "updated_at",
        ]


class FiscalYearCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = ["year", "label", "start_date", "end_date", "total_budget", "notes"]

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError(
                {"end_date": "La date de fin doit être après la date de début."}
            )
        if FiscalYear.objects.filter(year=attrs["year"]).exists():
            raise serializers.ValidationError({"year": f"Un exercice {attrs['year']} existe déjà."})
        return attrs


# ── Budget ────────────────────────────────────────────────
class BudgetListSerializer(serializers.ModelSerializer):
    available_amount = serializers.ReadOnlyField()
    consumption_rate = serializers.ReadOnlyField()
    is_alert_triggered = serializers.ReadOnlyField()
    is_overrun = serializers.ReadOnlyField()
    benefit_type_name = serializers.CharField(
        source="benefit_type.name", read_only=True, default=""
    )
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    fiscal_year_label = serializers.CharField(source="fiscal_year.label", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Budget
        fields = [
            "id",
            "code",
            "label",
            "fiscal_year",
            "fiscal_year_label",
            "benefit_type",
            "benefit_type_name",
            "department",
            "department_name",
            "status",
            "status_display",
            "allocated_amount",
            "paid_amount",
            "committed_amount",
            "reserved_amount",
            "available_amount",
            "consumption_rate",
            "is_alert_triggered",
            "is_overrun",
            "alert_threshold_pct",
            "anomaly_score",
        ]


class BudgetSerializer(BudgetListSerializer):
    approved_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta(BudgetListSerializer.Meta):
        fields = BudgetListSerializer.Meta.fields + [
            "approved_by",
            "approved_by_name",
            "approved_at",
            "notes",
            "variance_percent",
            "prediction_data",
            "created_at",
            "updated_at",
            "created_by_name",
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class BudgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            "code",
            "label",
            "fiscal_year",
            "benefit_type",
            "department",
            "allocated_amount",
            "alert_threshold_pct",
            "notes",
        ]

    def validate_allocated_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant alloué doit être positif.")
        return value

    def validate_code(self, value):
        return value.upper().strip()


# ── Payment ───────────────────────────────────────────────
class PaymentListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_matricule = serializers.CharField(source="employee.matricule", read_only=True)
    department_name = serializers.CharField(
        source="employee.department.name", read_only=True, default=""
    )
    benefit_type_name = serializers.CharField(source="benefit.benefit_type.name", read_only=True)
    benefit_ref = serializers.CharField(source="benefit.reference", read_only=True)
    budget_code = serializers.CharField(source="budget.code", read_only=True, default="")
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    method_display = serializers.CharField(source="get_payment_method_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "reference",
            "employee",
            "employee_name",
            "employee_matricule",
            "department_name",
            "benefit",
            "benefit_ref",
            "benefit_type_name",
            "budget",
            "budget_code",
            "amount",
            "fees",
            "net_amount",
            "status",
            "status_display",
            "payment_method",
            "method_display",
            "bank_reference",
            "scheduled_date",
            "executed_date",
            "anomaly_flag",
            "anomaly_score",
            "created_at",
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()


class PaymentSerializer(PaymentListSerializer):
    approved_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    fiscal_year_label = serializers.CharField(source="fiscal_year.label", read_only=True)

    class Meta(PaymentListSerializer.Meta):
        fields = PaymentListSerializer.Meta.fields + [
            "fiscal_year",
            "fiscal_year_label",
            "bank_name",
            "bank_account",
            "value_date",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "accounting_entry",
            "cost_center",
            "notes",
            "risk_indicators",
            "updated_at",
            "created_by_name",
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class PaymentCreateSerializer(serializers.Serializer):
    benefit_id = serializers.UUIDField()
    budget_id = serializers.UUIDField(required=False, allow_null=True)
    fiscal_year_id = serializers.UUIDField(required=False, allow_null=True)
    payment_method = serializers.ChoiceField(
        choices=[
            ("virement", "Virement"),
            ("cheque", "Chèque"),
            ("caisse", "Caisse"),
            ("ccp", "CCP"),
        ],
        default="virement",
    )
    bank_account = serializers.CharField(max_length=50, required=False, allow_blank=True)
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class PaymentMarkPaidSerializer(serializers.Serializer):
    bank_reference = serializers.CharField(max_length=100, min_length=3)
    executed_date = serializers.DateField(required=False, allow_null=True)
    paid_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True
    )

    def validate_paid_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Le montant payé doit être positif.")
        return value


class PaymentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5)


# ── PaymentBatch ──────────────────────────────────────────
class PaymentBatchSerializer(BaseModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    fiscal_year_label = serializers.CharField(source="fiscal_year.label", read_only=True)
    method_display = serializers.CharField(source="get_payment_method_display", read_only=True)

    class Meta:
        model = PaymentBatch
        fields = [
            "id",
            "reference",
            "label",
            "fiscal_year",
            "fiscal_year_label",
            "status",
            "status_display",
            "payment_method",
            "method_display",
            "total_amount",
            "payment_count",
            "scheduled_date",
            "executed_date",
            "bank_reference",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference",
            "total_amount",
            "payment_count",
            "created_at",
            "updated_at",
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None


class BatchCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=200)
    fiscal_year_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(
        choices=[
            ("virement", "Virement"),
            ("cheque", "Chèque"),
            ("caisse", "Caisse"),
            ("ccp", "CCP"),
        ],
        default="virement",
    )
    payment_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


# ── FinancialEntry ────────────────────────────────────────
class FinancialEntrySerializer(serializers.ModelSerializer):
    entry_type_display = serializers.CharField(source="get_entry_type_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FinancialEntry
        fields = [
            "id",
            "entry_number",
            "entry_type",
            "entry_type_display",
            "label",
            "amount",
            "entry_date",
            "accounting_date",
            "debit_account",
            "credit_account",
            "payment",
            "budget",
            "created_by_name",
            "notes",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        return obj.created_by_user.get_full_name() if obj.created_by_user else "Système"


# ── FinancialAlert ────────────────────────────────────────
class FinancialAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source="get_alert_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = FinancialAlert
        fields = [
            "id",
            "alert_type",
            "alert_type_display",
            "severity",
            "severity_display",
            "title",
            "message",
            "is_read",
            "is_resolved",
            "ai_generated",
            "ai_confidence",
            "fiscal_year",
            "budget",
            "payment",
            "created_at",
        ]
