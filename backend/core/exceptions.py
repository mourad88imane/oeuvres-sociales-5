"""
============================================================
EXCEPTIONS — Gestion centralisée des erreurs API
============================================================
Format de réponse unifié pour toutes les erreurs.
"""

import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    """
    Handler d'exception global pour DRF.
    Toutes les erreurs API retournent un format JSON unifié :
    {
        "status": "error",
        "code": "ERROR_CODE",
        "message": "Message lisible",
        "errors": {...}  // Optionnel : détails des erreurs de validation
    }
    """
    # Appel au handler DRF par défaut
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "status": "error",
            "code": _get_error_code(exc, response),
            "message": _get_error_message(exc, response),
        }

        # Ajouter les détails de validation si présents
        if isinstance(response.data, dict) and any(
            key not in ("detail", "code") for key in response.data
        ):
            error_payload["errors"] = response.data
        elif hasattr(response, "data") and response.data:
            error_payload["errors"] = response.data

        # Logging des erreurs serveur
        if response.status_code >= 500:
            logger.error(
                "Server error",
                extra={
                    "status_code": response.status_code,
                    "exception": str(exc),
                    "path": (
                        context.get("request", {}).path
                        if hasattr(context.get("request", {}), "path")
                        else ""
                    ),
                },
            )
        elif response.status_code == 401:
            logger.warning("Unauthorized access attempt", extra={"exception": str(exc)})

        response.data = error_payload

    return response


def _get_error_code(exc, response) -> str:
    """Retourne un code d'erreur lisible par machine."""
    if hasattr(exc, "default_code"):
        return exc.default_code.upper()
    code_map = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_REQUIRED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
    }
    return code_map.get(response.status_code, "UNKNOWN_ERROR")


def _get_error_message(exc, response) -> str:
    """Retourne un message d'erreur lisible."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail:
            return str(detail[0])
    message_map = {
        400: "Les données soumises sont invalides.",
        401: "Authentification requise.",
        403: "Vous n'avez pas les permissions nécessaires.",
        404: "La ressource demandée n'existe pas.",
        405: "Méthode HTTP non autorisée.",
        429: "Trop de requêtes. Veuillez réessayer plus tard.",
        500: "Erreur interne du serveur.",
    }
    return message_map.get(response.status_code, "Une erreur s'est produite.")


# ── Exceptions métier personnalisées ─────────────────────
class BusinessLogicError(Exception):
    """Exception pour les erreurs de logique métier."""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class WorkflowTransitionError(BusinessLogicError):
    """Transition de workflow invalide."""

    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            f"Transition invalide : {from_state} → {to_state}", code="INVALID_WORKFLOW_TRANSITION"
        )


class InsufficientBudgetError(BusinessLogicError):
    """Budget insuffisant pour une prestation."""

    def __init__(self, required: float, available: float):
        super().__init__(
            f"Budget insuffisant. Requis: {required}, Disponible: {available}",
            code="INSUFFICIENT_BUDGET",
        )
