"""Liveness and readiness endpoints."""

from httpkit.response import text


def register(app, version="1.4.0"):
    def root(request):
        return text("dispatch %s" % version)

    def healthz(request):
        return {"status": "ok", "version": version}

    def routes(request):
        return {"routes": app.router.describe()}

    app.add_route("/", root, ("GET",), name="root")
    app.add_route("/healthz", healthz, ("GET",), name="healthz")
    app.add_route("/_routes", routes, ("GET",), name="routes")
