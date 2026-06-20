"""
============================================================
AUTHENTICATION SERIALIZERS
============================================================
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer JWT personnalisé.
    Ajoute des claims supplémentaires dans le token :
    role, full_name, email → disponibles côté frontend sans appel API.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Claims personnalisés dans le payload JWT
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        token["role"] = user.role
        token["must_change_password"] = user.must_change_password
        token["tenant_id"] = str(user.tenant_id) if user.tenant_id else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Vérifier que le compte est actif
        if not self.user.is_active:
            raise serializers.ValidationError(
                {"detail": "Ce compte est désactivé. Contactez l'administrateur."}
            )

        # Enrichir la réponse avec les infos utilisateur
        preferences = self.user.preferences or {}
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.get_full_name(),
            "role": self.user.role,
            "role_display": self.user.get_role_display(),
            "must_change_password": self.user.must_change_password,
            "avatar": self.user.avatar.url if self.user.avatar else None,
            "tenant_id": str(self.user.tenant_id) if self.user.tenant_id else None,
            "tenant_name": self.user.tenant.name if self.user.tenant else None,
            "preferences": {
                "language": preferences.get("language", "fr"),
                "theme": preferences.get("theme", "light"),
                "layout_direction": preferences.get("layout_direction", "ltr"),
            },
        }

        return data


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Format de réponse du refresh token."""

    access = serializers.CharField()
    user = serializers.DictField()


class LoginResponseSerializer(serializers.Serializer):
    """Format de réponse du login."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()


class LogoutSerializer(serializers.Serializer):
    """Blacklist du refresh token à la déconnexion."""

    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Token de rafraîchissement invalide ou expiré.")
        return value

    def save(self):
        self.token.blacklist()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Demande de reset de mot de passe."""

    email = serializers.EmailField()

    def validate_email(self, value):
        # Ne pas révéler si l'email existe ou non (sécurité)
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmation du reset avec token."""

    token = serializers.CharField()
    uid = serializers.CharField()
    new_password = serializers.CharField(min_length=10)
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Les mots de passe ne correspondent pas."}
            )
        return attrs
