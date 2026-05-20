"""Utilitaires pour le module d'authentification."""
from django.http import JsonResponse


def axes_lockout_response(request, credentials, *args, **kwargs):
    """
    Réponse personnalisée quand django-axes bloque un compte
    après trop de tentatives échouées.
    """
    return JsonResponse(
        {
            "status": "error",
            "code": "ACCOUNT_LOCKED",
            "message": (
                "Votre compte a été temporairement bloqué après plusieurs "
                "tentatives de connexion échouées. "
                "Veuillez réessayer dans 30 minutes ou contacter l'administrateur."
            ),
        },
        status=403,
    )
