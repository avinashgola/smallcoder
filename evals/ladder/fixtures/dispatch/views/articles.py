"""CRUD views for the article collection."""

from core.errors import BadRequest, UnsupportedMediaType
from httpkit.response import JsonResponse, no_content

from .store import Repository


def _json_body(request):
    if request.content_type not in (None, "application/json"):
        raise UnsupportedMediaType(request.content_type, "application/json")
    try:
        payload = request.json()
    except ValueError as exc:
        raise BadRequest("malformed JSON: %s" % exc) from None
    if not isinstance(payload, dict):
        raise BadRequest("expected a JSON object")
    return payload


def register(app, repository=None):
    """Attach the article routes to ``app``."""
    repo = repository if repository is not None else Repository()

    def index(request):
        items = repo.list(
            tag=request.query.get("tag"),
            limit=request.query.get_int("limit"),
            offset=request.query.get_int("offset", 0),
        )
        return {"items": items, "total": len(repo)}

    def create(request):
        record = repo.create(_json_body(request))
        response = JsonResponse(record, 201)
        response.headers.set("Location", "/articles/%d" % record["id"])
        return response

    def detail(request):
        return repo.get(request.param("article_id"))

    def replace(request):
        return repo.update(request.param("article_id"), _json_body(request))

    def remove(request):
        repo.delete(request.param("article_id"))
        return no_content()

    app.add_route("/articles", index, ("GET",), name="articles.index")
    app.add_route("/articles", create, ("POST",), name="articles.create")
    app.add_route("/articles/<int:article_id>", detail, ("GET",),
                  name="articles.detail")
    app.add_route("/articles/<int:article_id>", replace, ("PUT",),
                  name="articles.replace")
    app.add_route("/articles/<int:article_id>", remove, ("DELETE",),
                  name="articles.delete")
    return repo
