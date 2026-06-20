from rest_framework import serializers

from shared.workflow.models import WorkflowState, WorkflowTransition, WorkflowTransitionRole


class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = [
            "id", "app_label", "model_name", "state_id",
            "label_fr", "label_ar", "color",
            "is_initial", "is_final", "display_order", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowTransitionRoleSerializer(serializers.ModelSerializer):
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = WorkflowTransitionRole
        fields = ["id", "transition", "role", "role_slug", "role_name", "permission", "created_at"]
        read_only_fields = ["id", "created_at"]


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    from_state_id = serializers.CharField(source="from_state.state_id", read_only=True)
    from_state_label = serializers.CharField(source="from_state.label_fr", read_only=True)
    to_state_id = serializers.CharField(source="to_state.state_id", read_only=True)
    to_state_label = serializers.CharField(source="to_state.label_fr", read_only=True)
    allowed_roles = WorkflowTransitionRoleSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowTransition
        fields = [
            "id", "app_label", "model_name",
            "from_state", "from_state_id", "from_state_label",
            "to_state", "to_state_id", "to_state_label",
            "name", "label_fr", "label_ar",
            "requires_reason", "is_reversal", "severity",
            "display_order", "is_active",
            "allowed_roles",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowTransitionRoleWriteSerializer(serializers.Serializer):
    role = serializers.UUIDField()
    permission = serializers.UUIDField(required=False, allow_null=True)
