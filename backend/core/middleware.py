import uuid

from . import log_context


class CsrfExemptApiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            request.csrf_processing_done = True
        return self.get_response(request)


class CorrelationIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = (
            request.META.get("HTTP_X_CORRELATION_ID")
            or request.META.get("HTTP_X_REQUEST_ID")
            or str(uuid.uuid4())
        )
        request.correlation_id = correlation_id

        if not hasattr(request, "request_id") or not request.request_id:
            request.request_id = str(uuid.uuid4())

        log_context.correlation_id.set(correlation_id)
        log_context.request_id.set(request.request_id)

        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id
        return response
