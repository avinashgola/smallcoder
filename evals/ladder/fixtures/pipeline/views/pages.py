"""The handful of HTML and diagnostic pages."""

from message.response import html_response, text_response
from middleware.context import context_of


def render_list(tasks):
    rows = "".join(
        "<li>%s &mdash; %s</li>" % (task["title"], task["state"])
        for task in tasks)
    return "<ul>%s</ul>" % rows


def register(app, store):
    def home(request):
        return html_response("<h1>Tasks</h1>" + render_list(store.list()))

    def board(request):
        state = request.param("state")
        return html_response("<h1>%s</h1>%s" % (state,
                                                render_list(store.list(state))))

    def health(request):
        return {"status": "ok", "tasks": len(store)}

    def whoami(request):
        context = context_of(request)
        return text_response(context.get("request_id", "untracked"))

    def layers(request):
        return {"layers": app.middleware.labels(), "rules": app.routes.describe()}

    app.get("/", home, name="pages.home")
    app.get("/board/{state}", board, name="pages.board")
    app.get("/health", health, name="pages.health")
    app.get("/whoami", whoami, name="pages.whoami")
    app.get("/_layers", layers, name="pages.layers")
