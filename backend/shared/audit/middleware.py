"""
============================================================
AUDIT MIDDLEWARE — Middleware de traçabilité automatique
============================================================
Injecte un request_id unique dans chaque requête HTTP.
Ce request_id permet de corréler tous les logs d'une même
requête dans les systèmes d'analyse (ELK, Grafana Loki, etc.)
"""

import logging
import uuid

logger = logging.getLogger("audit")


class AuditMiddleware:
    """
    Middleware qui ajoute un identifiant unique à chaque requête.
    Utilisé pour :
    - Corrélation des logs (tracer une requête complète)
    - Contexte pour l'audit trail
    - Debugging en production
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Générer un ID unique pour cette requête
        request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        request.request_id = request_id

        # Log de la requête entrante
        if not request.path.startswith("/admin/"):
            logger.info(
                "HTTP Request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "user": str(request.user) if hasattr(request, "user") else "anonymous",
                    "ip": self._get_ip(request),
                },
            )

        response = self.get_response(request)

        # Ajouter le request_id dans la réponse pour le debugging frontend
        response["X-Request-ID"] = request_id

        return response

    def _get_ip(self, request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
