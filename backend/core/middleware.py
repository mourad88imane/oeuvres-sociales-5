class CsrfExemptApiMiddleware:
    """Skip CSRF for all /api/ routes (JWT-only API, no session auth)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            request.csrf_processing_done = True
        return self.get_response(request)
