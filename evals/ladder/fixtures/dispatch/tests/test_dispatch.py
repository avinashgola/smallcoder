from core.app import Application
from core.testing import Client, payload_of
from views import articles, echo, errors, health
from views.store import SEED, Repository


def build():
    app = Application()
    health.register(app)
    articles.register(app, Repository(SEED))
    echo.register(app)
    errors.register(app)
    return Client(app)


def test_collection_index():
    response = build().get("/articles")
    assert response.status == 200
    assert payload_of(response)["total"] == 3


def test_collection_accepts_posts():
    response = build().post("/articles", json_body={"title": "New", "body": "x"})
    assert response.status == 201
    assert response.headers["Location"] == "/articles/4"


def test_detail_route():
    response = build().get("/articles/2")
    assert payload_of(response)["title"] == "Converters"


def test_missing_record_is_404():
    assert build().get("/articles/99").status == 404


def test_unknown_path_uses_the_custom_renderer():
    response = build().get("/nothing/here")
    assert response.status == 404
    assert payload_of(response) == {"error": "not_found", "path": "/nothing/here"}


def test_unsupported_method_lists_every_method_for_the_path():
    response = build().delete("/articles")
    assert response.status == 405
    assert response.headers["Allow"] == "GET, HEAD, POST"


def test_greedy_route_captures_the_remainder():
    payload = payload_of(build().get("/files/docs/a/b.txt"))
    assert payload["rest"] == "docs/a/b.txt"


def test_head_requests_have_no_body():
    client = build()
    response = client.open("HEAD", "/healthz")
    assert response.status == 200
    assert response.body == b""
