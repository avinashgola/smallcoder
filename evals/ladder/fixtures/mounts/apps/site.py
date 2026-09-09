"""The composed site: a host application with three mounted applications."""

from kernel.application import Application
from mounting.report import describe, render

from .admin import build_admin
from .api import build_api
from .docs import build_docs


def build_site(**settings):
    """The whole site, wired the way the service starts it."""
    app = Application("site", **settings)

    def home(request):
        return {"app": "site", "mounts": app.mounts.prefixes()}

    def health(request):
        return {"status": "ok"}

    def mount_map(request):
        return {"tree": describe(app)}

    def mount_text(request):
        return render(app)

    app.get("/", home, name="site.home")
    app.get("/health", health, name="site.health")
    app.get("/_mounts", mount_map, name="site.mounts")
    app.get("/_mounts.txt", mount_text, name="site.mounts.text")
    app.mount("/admin", build_admin(), name="admin")
    app.mount("/api", build_api(), name="api")
    app.mount("/docs", build_docs(), name="docs")
    return app
