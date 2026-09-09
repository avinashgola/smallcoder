"""Custom renderers for the statuses the API reports most often."""

from httpkit.response import JsonResponse, text


def register(app):
    @app.error_handler(404)
    def not_found(request, error):
        return JsonResponse({"error": "not_found", "path": request.path}, 404)

    @app.error_handler(415)
    def unsupported(request, error):
        return text(error.detail, 415)
