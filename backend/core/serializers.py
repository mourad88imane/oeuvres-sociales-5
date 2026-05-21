"""
============================================================
SERIALIZERS DE BASE — Fondation pour tous les serializers
============================================================
"""

from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Serializer de base avec champs communs automatiques.
    Tous les serializers du projet héritent de cette classe.
    """

    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        abstract = True
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_request_user(self):
        """Retourne l'utilisateur de la requête courante."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user
        return None

    def create(self, validated_data):
        """Auto-assignation de created_by."""
        user = self.get_request_user()
        if user and not user.is_anonymous:
            validated_data["created_by"] = user
            validated_data["updated_by"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Auto-assignation de updated_by."""
        user = self.get_request_user()
        if user and not user.is_anonymous:
            validated_data["updated_by"] = user
        return super().update(instance, validated_data)


class SuccessResponseSerializer(serializers.Serializer):
    """Format de réponse succès standard."""

    status = serializers.CharField(default="success")
    message = serializers.CharField()
    data = serializers.DictField(required=False)
