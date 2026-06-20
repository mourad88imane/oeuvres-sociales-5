from rest_framework import serializers

from core.serializers import BaseModelSerializer

from .models import Loan, LoanAttachment, LoanComment
from .workflow import loan_workflow


class LoanAttachmentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    doc_type_display = serializers.CharField(source="get_doc_type_display", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LoanAttachment
        fields = [
            "id", "original_name", "doc_type", "doc_type_display", "description",
            "file_size", "file_size_display", "mime_type", "uploaded_by_name",
            "file_url", "created_at",
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    doc_type = serializers.ChoiceField(choices=LoanAttachment.DocType.choices, default="other")
    description = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate_file(self, value):
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Fichier trop volumineux (max 10 Mo).")
        return value


class LoanCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_comment_type_display", read_only=True)

    class Meta:
        model = LoanComment
        fields = [
            "id", "author_name", "author_role", "comment_type", "type_display",
            "content", "workflow_state_at_time", "created_at",
        ]
        read_only_fields = ["id", "author_name", "author_role", "workflow_state_at_time", "created_at"]

    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else "Système"

    def get_author_role(self, obj):
        return obj.author.get_role_display() if obj.author else ""


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=2)
    comment_type = serializers.ChoiceField(choices=LoanComment.CommentType.choices, default="internal")


class WorkflowLogSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    from_state = serializers.CharField()
    from_state_label = serializers.SerializerMethodField()
    to_state = serializers.CharField()
    to_state_label = serializers.SerializerMethodField()
    transition_name = serializers.CharField()
    actor_email = serializers.CharField()
    actor_role = serializers.CharField()
    reason = serializers.CharField()
    duration_seconds = serializers.FloatField(allow_null=True)
    duration_label = serializers.ReadOnlyField()
    is_reversal = serializers.BooleanField()
    severity = serializers.CharField()
    timestamp = serializers.DateTimeField()

    def get_from_state_label(self, obj):
        return loan_workflow.get_state_label(obj.from_state)

    def get_to_state_label(self, obj):
        return loan_workflow.get_state_label(obj.to_state)


class LoanListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_matricule = serializers.CharField(source="employee.matricule", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)
    state_label = serializers.ReadOnlyField(source="workflow_state_label")
    state_config = serializers.SerializerMethodField()
    amount_display = serializers.ReadOnlyField()

    class Meta:
        model = Loan
        fields = [
            "id", "reference", "reason", "workflow_state", "state_label", "state_config",
            "employee", "employee_name", "employee_matricule", "department_name",
            "requested_amount", "approved_amount", "amount_display",
            "submitted_at", "validated_at", "paid_at", "created_at", "updated_at",
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_state_config(self, obj):
        return loan_workflow.STATES.get(obj.workflow_state, {})


class LoanDetailSerializer(BaseModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_matricule = serializers.CharField(source="employee.matricule", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)
    state_label = serializers.ReadOnlyField(source="workflow_state_label")
    state_config = serializers.SerializerMethodField()
    amount_display = serializers.ReadOnlyField()
    instalment_display = serializers.ReadOnlyField()
    validated_by_name = serializers.SerializerMethodField()
    paid_by_name = serializers.SerializerMethodField()
    attachments = LoanAttachmentSerializer(many=True, read_only=True)
    comments = LoanCommentSerializer(many=True, read_only=True)
    available_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id", "reference", "reason", "description", "workflow_state", "state_label",
            "state_config", "employee", "employee_name", "employee_matricule",
            "department_name", "requested_amount", "approved_amount", "paid_amount",
            "amount_display", "monthly_instalment", "instalment_count", "instalment_display",
            "submitted_at", "validated_at", "paid_at", "rejected_at",
            "validated_by_name", "paid_by_name", "rejection_reason", "payment_reference",
            "attachments", "comments", "available_transitions",
            "last_transition_at", "last_transition_reason",
            "created_at", "updated_at", "created_by_name",
        ]
        read_only_fields = ["id", "reference", "created_at", "updated_at"]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_validated_by_name(self, obj):
        return obj.validated_by.get_full_name() if obj.validated_by else None

    def get_paid_by_name(self, obj):
        return obj.paid_by.get_full_name() if obj.paid_by else None

    def get_state_config(self, obj):
        return loan_workflow.STATES.get(obj.workflow_state, {})

    def get_available_transitions(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return []
        from .services import LoanService
        return LoanService().get_available_transitions(obj, request.user)


class LoanCreateSerializer(BaseModelSerializer):
    class Meta:
        model = Loan
        fields = [
            "employee", "requested_amount", "reason", "description",
        ]

    def validate_requested_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value


class LoanUpdateSerializer(BaseModelSerializer):
    class Meta:
        model = Loan
        fields = [
            "reason", "description", "requested_amount",
        ]

    def validate_requested_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value


class TransitionSerializer(serializers.Serializer):
    to_state = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
    approved_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True
    )
    monthly_instalment = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    instalment_count = serializers.IntegerField(required=False, allow_null=True)
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    paid_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True
    )
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_to_state(self, value):
        if value not in loan_workflow.STATES:
            raise serializers.ValidationError(f"État '{value}' inconnu.")
        return value
