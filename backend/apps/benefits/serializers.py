"""Benefits serializers."""
from rest_framework import serializers
from core.serializers import BaseModelSerializer
from .models import Benefit, BenefitType, BenefitAttachment, BenefitComment
from .workflow import benefit_workflow


# ── BenefitType ───────────────────────────────────────────
class BenefitTypeSerializer(BaseModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    class Meta:
        model  = BenefitType
        fields = ["id","code","name","category","category_display","description","is_active",
                  "max_amount","min_seniority_years","max_per_year",
                  "requires_attachments","required_attachments_description",
                  "target_processing_days","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]

class BenefitTypeListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    class Meta:
        model  = BenefitType
        fields = ["id","code","name","category","category_display","max_amount","is_active","requires_attachments"]


# ── Attachment ────────────────────────────────────────────
class BenefitAttachmentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    doc_type_display  = serializers.CharField(source="get_doc_type_display", read_only=True)
    uploaded_by_name  = serializers.SerializerMethodField()
    file_url          = serializers.SerializerMethodField()
    class Meta:
        model  = BenefitAttachment
        fields = ["id","original_name","doc_type","doc_type_display","description",
                  "file_size","file_size_display","mime_type","uploaded_by_name","file_url","created_at"]
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None
    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class AttachmentUploadSerializer(serializers.Serializer):
    file        = serializers.FileField()
    doc_type    = serializers.ChoiceField(choices=BenefitAttachment.DocType.choices, default="other")
    description = serializers.CharField(max_length=300, required=False, allow_blank=True)
    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  # 10 Mo
        if value.size > max_size:
            raise serializers.ValidationError("Fichier trop volumineux (max 10 Mo).")
        allowed = ("application/pdf","image/jpeg","image/png","image/webp",
                   "application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if hasattr(value,"content_type") and value.content_type not in allowed:
            raise serializers.ValidationError("Type de fichier non autorisé (PDF, image, Word).")
        return value


# ── Comment ───────────────────────────────────────────────
class BenefitCommentSerializer(serializers.ModelSerializer):
    author_name  = serializers.SerializerMethodField()
    author_role  = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_comment_type_display", read_only=True)
    class Meta:
        model  = BenefitComment
        fields = ["id","author_name","author_role","comment_type","type_display",
                  "content","workflow_state_at_time","created_at"]
        read_only_fields = ["id","author_name","author_role","workflow_state_at_time","created_at"]
    def get_author_name(self, obj): return obj.author.get_full_name() if obj.author else "Système"
    def get_author_role(self, obj): return obj.author.get_role_display() if obj.author else ""

class CommentCreateSerializer(serializers.Serializer):
    content      = serializers.CharField(min_length=2)
    comment_type = serializers.ChoiceField(choices=BenefitComment.CommentType.choices, default="internal")


# ── WorkflowLog ───────────────────────────────────────────
class WorkflowLogSerializer(serializers.Serializer):
    id               = serializers.UUIDField()
    from_state       = serializers.CharField()
    from_state_label = serializers.SerializerMethodField()
    to_state         = serializers.CharField()
    to_state_label   = serializers.SerializerMethodField()
    transition_name  = serializers.CharField()
    actor_email      = serializers.CharField()
    actor_role       = serializers.CharField()
    reason           = serializers.CharField()
    duration_seconds = serializers.FloatField(allow_null=True)
    duration_label   = serializers.ReadOnlyField()
    is_reversal      = serializers.BooleanField()
    severity         = serializers.CharField()
    timestamp        = serializers.DateTimeField()
    def get_from_state_label(self, obj):
        return benefit_workflow.get_state_label(obj.from_state)
    def get_to_state_label(self, obj):
        return benefit_workflow.get_state_label(obj.to_state)


# ── Benefit List ──────────────────────────────────────────
class BenefitListSerializer(serializers.ModelSerializer):
    employee_name      = serializers.SerializerMethodField()
    employee_matricule = serializers.CharField(source="employee.matricule", read_only=True)
    department_name    = serializers.CharField(source="employee.department.name", read_only=True)
    benefit_type_name  = serializers.CharField(source="benefit_type.name", read_only=True)
    benefit_type_code  = serializers.CharField(source="benefit_type.code", read_only=True)
    benefit_category   = serializers.CharField(source="benefit_type.category", read_only=True)
    state_label        = serializers.ReadOnlyField(source="workflow_state_label")
    state_config       = serializers.SerializerMethodField()
    priority_display   = serializers.CharField(source="get_priority_display", read_only=True)
    is_overdue         = serializers.ReadOnlyField()
    processing_days    = serializers.ReadOnlyField()
    attachments_count  = serializers.ReadOnlyField()
    amount_display     = serializers.ReadOnlyField()

    class Meta:
        model  = Benefit
        fields = [
            "id","reference","title","workflow_state","state_label","state_config",
            "employee","employee_name","employee_matricule","department_name",
            "benefit_type","benefit_type_name","benefit_type_code","benefit_category",
            "requested_amount","approved_amount","paid_amount","amount_display",
            "priority","priority_display","is_overdue","processing_days",
            "submitted_at","validated_at","paid_at","due_date",
            "attachments_count","ai_anomaly_flag","risk_score",
            "created_at","updated_at",
        ]

    def get_employee_name(self, obj): return obj.employee.get_full_name()
    def get_state_config(self, obj):
        return benefit_workflow.STATES.get(obj.workflow_state, {})


# ── Benefit Detail ────────────────────────────────────────
class BenefitDetailSerializer(BaseModelSerializer):
    employee_name      = serializers.SerializerMethodField()
    employee_matricule = serializers.CharField(source="employee.matricule", read_only=True)
    department_name    = serializers.CharField(source="employee.department.name", read_only=True)
    benefit_type_info  = BenefitTypeListSerializer(source="benefit_type", read_only=True)
    state_label        = serializers.ReadOnlyField(source="workflow_state_label")
    state_config       = serializers.SerializerMethodField()
    priority_display   = serializers.CharField(source="get_priority_display", read_only=True)
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    is_overdue         = serializers.ReadOnlyField()
    processing_days    = serializers.ReadOnlyField()
    amount_display     = serializers.ReadOnlyField()
    validated_by_name  = serializers.SerializerMethodField()
    paid_by_name       = serializers.SerializerMethodField()
    attachments        = BenefitAttachmentSerializer(many=True, read_only=True)
    comments           = BenefitCommentSerializer(many=True, read_only=True)
    available_transitions = serializers.SerializerMethodField()

    class Meta:
        model  = Benefit
        fields = [
            "id","reference","title","description",
            "workflow_state","state_label","state_config",
            "employee","employee_name","employee_matricule","department_name",
            "benefit_type","benefit_type_info","beneficiary",
            "requested_amount","approved_amount","paid_amount","amount_display",
            "priority","priority_display","is_overdue","processing_days",
            "submitted_at","validated_at","paid_at","rejected_at","due_date",
            "validated_by_name","paid_by_name",
            "rejection_reason","payment_reference","payment_method","payment_method_display",
            "internal_notes","ai_score","ai_anomaly_flag","risk_score",
            "attachments","comments","available_transitions",
            "last_transition_at","last_transition_reason",
            "created_at","updated_at","created_by_name",
        ]
        read_only_fields = ["id","reference","created_at","updated_at"]

    def get_employee_name(self, obj):   return obj.employee.get_full_name()
    def get_validated_by_name(self, obj): return obj.validated_by.get_full_name() if obj.validated_by else None
    def get_paid_by_name(self, obj):    return obj.paid_by.get_full_name() if obj.paid_by else None
    def get_state_config(self, obj):    return benefit_workflow.STATES.get(obj.workflow_state, {})
    def get_available_transitions(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return []
        from apps.benefits.services import BenefitService
        return BenefitService().get_available_transitions(obj, request.user)


# ── Benefit Create / Update ───────────────────────────────
class BenefitCreateSerializer(BaseModelSerializer):
    class Meta:
        model  = Benefit
        fields = ["employee","benefit_type","beneficiary","title","description",
                  "requested_amount","priority","due_date","internal_notes"]

    def validate_requested_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value

    def validate(self, attrs):
        btype  = attrs.get("benefit_type")
        amount = attrs.get("requested_amount", 0)
        if btype and btype.max_amount and amount > btype.max_amount:
            raise serializers.ValidationError({
                "requested_amount": f"Dépasse le plafond de {btype.max_amount:,.0f} DZD pour ce type."
            })
        return attrs


class BenefitUpdateSerializer(BaseModelSerializer):
    class Meta:
        model  = Benefit
        fields = ["title","description","requested_amount","priority","due_date","internal_notes","beneficiary"]

    def validate_requested_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value


# ── Transition ────────────────────────────────────────────
class TransitionSerializer(serializers.Serializer):
    to_state         = serializers.CharField()
    reason           = serializers.CharField(required=False, allow_blank=True)
    approved_amount  = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    payment_reference= serializers.CharField(max_length=100, required=False, allow_blank=True)
    paid_amount      = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    comment          = serializers.CharField(required=False, allow_blank=True)

    def validate_to_state(self, value):
        if value not in benefit_workflow.STATES:
            raise serializers.ValidationError(f"État '{value}' inconnu.")
        return value
