"""Diagnostic views that reflect the parsed request back to the caller."""

from httpkit.response import JsonResponse


def register(app):
    def echo(request):
        return JsonResponse({
            "method": request.method,
            "path": request.path,
            "query": request.query.to_dict(),
            "headers": dict(request.headers.to_wire()),
            "length": request.content_length,
        })

    def echo_body(request):
        return {"body": request.text(), "type": request.content_type}

    def capture(request):
        return {"rest": request.param("rest", ""), "route": request.state["route"]}

    app.add_route("/echo", echo, ("GET", "POST"), name="echo")
    app.add_route("/echo/body", echo_body, ("POST",), name="echo.body")
    app.add_route("/files/<path:rest>", capture, ("GET",), name="files")
