"""
Authentication URL Configuration.
Toutes les routes d'authentification.
"""

from django.urls import path

from .views import LoginView, LogoutView, MeView, TokenRefreshView, UpdatePreferencesView, VerifyTokenView

app_name = "auth"

urlpatterns = [
    # Login → retourne access + refresh tokens
    path("login/", LoginView.as_view(), name="login"),
    # Logout → blacklist le refresh token
    path("logout/", LogoutView.as_view(), name="logout"),
    # Refresh → nouveau access token depuis le refresh token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Me → profil complet de l'utilisateur connecté
    path("me/", MeView.as_view(), name="me"),
    # Verify → vérification de la validité du token
    path("verify/", VerifyTokenView.as_view(), name="verify"),
    # Preferences → mise à jour des préférences utilisateur
    path("preferences/", UpdatePreferencesView.as_view(), name="preferences"),
]
