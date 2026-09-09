import pytest

from core.errors import NotFound
from routing.converters import ConversionError, get_converter
from routing.patterns import Pattern, normalize_path, split_path
from routing.router import Router
from routing.urls import UrlBuilder, encode_query


def handler(request):
    return "ok"


def test_normalize_path():
    assert normalize_path("articles/") == "/articles"
    assert normalize_path("/a//b/") == "/a/b"
    assert normalize_path("/") == "/"
    assert split_path("/a/b") == ["a", "b"]


def test_static_pattern():
    pattern = Pattern("/articles")
    assert pattern.match("/articles") == {}
    assert pattern.match("/articles/1") is None


def test_typed_pattern():
    pattern = Pattern("/articles/<int:article_id>")
    assert pattern.match("/articles/12") == {"article_id": 12}
    assert pattern.match("/articles/abc") is None


def test_greedy_pattern():
    pattern = Pattern("/files/<path:rest>")
    assert pattern.match("/files/a/b/c.txt") == {"rest": "a/b/c.txt"}


def test_greedy_must_be_last():
    with pytest.raises(ValueError):
        Pattern("/files/<path:rest>/meta")


def test_converters():
    assert get_converter("slug").to_python("hello-world") == "hello-world"
    with pytest.raises(ConversionError):
        get_converter("slug").to_python("Hello World")
    with pytest.raises(ConversionError):
        get_converter("int").to_python("-2")


def test_router_matches_in_registration_order():
    router = Router()
    router.add("/articles/latest", handler, name="latest")
    router.add("/articles/<slug:name>", handler, name="by_name")
    route, params = router.match("GET", "/articles/latest")
    assert route.name == "latest"
    assert params == {}


def test_router_reports_unknown_paths():
    router = Router()
    router.add("/articles", handler)
    with pytest.raises(NotFound):
        router.match("GET", "/nope")


def test_methods_for_collects_every_route():
    router = Router()
    router.add("/articles", handler, ("GET",), name="a")
    router.add("/articles", handler, ("POST",), name="b")
    assert router.methods_for("/articles") == ["GET", "HEAD", "POST"]


def test_url_building():
    router = Router()
    router.add("/articles/<int:article_id>", handler, name="detail")
    urls = UrlBuilder(router)
    assert urls.url_for("detail", article_id=7) == "/articles/7"
    assert encode_query({"tag": "a b"}) == "?tag=a%20b"
