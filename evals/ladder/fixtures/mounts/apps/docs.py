"""The handbook, served as very plain HTML."""

from kernel.application import Application
from kernel.errors import NotFound
from net.response import html_response
from routes.urls import url_for

from .data import PAGES


def build_docs(settings=None):
    app = Application("docs", settings)

    def index(request):
        links = "".join(
            '<li><a href="%s">%s</a></li>'
            % (url_for(app, "docs.page", {"page": name},
                       script_name=request.script_name), name)
            for name in sorted(PAGES))
        return html_response("<h1>Handbook</h1><ul>%s</ul>" % links)

    def page(request):
        name = request.var("page", "")
        if name not in PAGES:
            raise NotFound(request.full_path)
        return html_response("<h1>%s</h1><p>%s</p>" % (name, PAGES[name]))

    app.get("/", index, name="docs.index")
    app.get("/{page}", page, name="docs.page")
    return app
