"""Generic API viewsets, mixins, and response helpers.

Usage across all projects:
    from shared.api.viewsets import GenericModelViewSet
    from shared.api.responses import success_response, error_response
    from shared.api.mixins import AuditMixin, FilterMixin
"""
from typing import Optional

from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message: str = "", status_code: int = 200) -> Response:
    """Standard success response."""
    payload = {"status": "success"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def error_response(
    message: str = "Une erreur s'est produite.",
    code: str = "ERROR",
    errors: Optional[dict] = None,
    status_code: int = 400,
) -> Response:
    """Standard error response."""
    payload = {"status": "error", "code": code, "message": message}
    if errors:
        payload["errors"] = errors
    return Response(payload, status=status_code)


def paginated_response(data, paginator) -> Response:
    """Paginated response following project conventions."""
    return Response({
        "status": "success",
        "pagination": {
            "count": paginator.page.paginator.count,
            "page": paginator.page.number,
            "page_size": paginator.get_page_size(paginator.request),
            "total_pages": paginator.page.paginator.num_pages,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        },
        "results": data,
    })
