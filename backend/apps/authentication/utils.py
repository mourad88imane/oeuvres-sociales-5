"""Utilitaires pour le module d'authentification."""

from urllib.parse import urlparse

from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


def axes_lockout_response(request, credentials, *args, **kwargs):
    """
    Réponse personnalisée quand django-axes bloque un compte
    après trop de tentatives échouées.

    - Pour /admin/* → redirige vers la page de login admin avec un message d'erreur
    - Pour l'API → retourne du JSON comme avant
    """
    path = urlparse(request.build_absolute_uri()).path

    # Si la requête concerne l'interface d'administration Django
    if path.startswith("/admin/"):
        login_url = reverse("admin:login")
        return redirect(f"{login_url}?locked=1")

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
