"""
============================================================
AUTHENTICATION VIEWS — Login, Logout, Refresh, Me
============================================================
"""
import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.serializers import UserSerializer
from shared.audit.services import AuditService
from shared.ai.models import AIEvent
from .serializers import CustomTokenObtainPairSerializer, LogoutSerializer

User = get_user_model()
logger = logging.getLogger("apps.authentication")
audit = AuditService()


class LoginThrottle(AnonRateThrottle):
    """Throttle spécifique pour le login : 10 tentatives/minute."""
    rate = "10/minute"
    scope = "login"


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Corps : { "email": "...", "password": "..." }
    Réponse : { access, refresh, user }
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        user = serializer.user
        ip = self._get_client_ip(request)

        # Mise à jour des métadonnées de connexion
        User.objects.filter(pk=user.pk).update(
            last_login_ip=ip,
            failed_login_count=0,
        )

        # Log d'audit
        audit.log_login(user=user, ip=ip, success=True)

        # Log AI event for behavior analysis
        try:
            AIEvent.objects.create(
                user=user,
                user_email=user.email,
                user_role=getattr(user, "role", ""),
                event_category=AIEvent.EventCategory.LOGIN,
                event_name="user_login",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                properties={"method": "password"},
            )
        except Exception:
            logger.exception("Failed to log AI login event")

        logger.info("User logged in", extra={"user_id": str(user.id), "ip": ip})

        return Response({
            "status": "success",
            "message": "Connexion réussie.",
            **serializer.validated_data,
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Corps : { "refresh": "..." }
    Blacklist le refresh token → déconnexion complète.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        audit.log_logout(user=request.user)

        try:
            AIEvent.objects.create(
                user=request.user,
                user_email=request.user.email,
                user_role=getattr(request.user, "role", ""),
                event_category=AIEvent.EventCategory.LOGIN,
                event_name="user_logout",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except Exception:
            logger.exception("Failed to log AI logout event")

        logger.info("User logged out", extra={"user_id": str(request.user.id)})

        return Response({
            "status": "success",
            "message": "Déconnexion réussie.",
        }, status=status.HTTP_200_OK)


class TokenRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/
    Corps : { "refresh": "..." }
    Retourne un nouveau access token + nouveau refresh token.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {
                "status": "success",
                **response.data,
            }
        return response


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    Retourne le profil complet de l'utilisateur connecté.
    Utile pour recharger les données après navigation.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response({
            "status": "success",
            "data": serializer.data,
        })


class VerifyTokenView(APIView):
    """
    GET /api/v1/auth/verify/
    Vérifie si le token est valide. Utilisé par le frontend au démarrage.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "status": "success",
            "valid": True,
            "user": {
                "id": str(request.user.id),
                "email": request.user.email,
                "role": request.user.role,
                "must_change_password": request.user.must_change_password,
            },
        })
