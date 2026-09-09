from message.headers import HeaderMap, split_list
from message.mediatype import parse_media_type
from message.request import Request
from message.response import Response, json_response
from message.status import may_have_body, reason
from message.urls import join, normalize, parse_query, starts_with


def test_header_map_is_case_insensitive():
    headers = HeaderMap({"Content-Type": "text/plain"})
    assert headers["content-type"] == "text/plain"
    headers.set("CONTENT-TYPE", "text/html")
    assert headers.items() == [("CONTENT-TYPE", "text/html")]


def test_header_map_keeps_repeats():
    headers = HeaderMap()
    headers.add("Set-Cookie", "a=1")
    headers.add("Set-Cookie", "b=2")
    assert headers.get_all("set-cookie") == ["a=1", "b=2"]
    assert len(headers) == 2


def test_split_list():
    assert split_list("a, b ,, c") == ["a", "b", "c"]


def test_media_type_parsing_and_matching():
    media = parse_media_type("application/json; charset=utf-8")
    assert media.essence == "application/json"
    assert media.charset == "utf-8"
    assert media.matches("application/*")
    assert not media.matches("text/html")
    assert parse_media_type("  ") is None


def test_url_helpers():
    assert normalize("/a//b/") == "/a/b"
    assert join("api", "/tasks/") == "/api/tasks"
    assert starts_with("/api/tasks", "/api")
    assert not starts_with("/apibits", "/api")
    assert parse_query("?a=1&b=two+words") == [("a", "1"), ("b", "two words")]


def test_request_parsing():
    request = Request("post", "/api/tasks/", {"Content-Type": "application/json"},
                      "state=todo", b'{"title":"x"}')
    assert request.method == "POST"
    assert request.path == "/api/tasks"
    assert request.arg("state") == "todo"
    assert request.json() == {"title": "x"}


def test_response_seal():
    response = json_response({"a": 1}, 201).seal()
    assert response.headers["Content-Length"] == "7"
    assert response.json() == {"a": 1}
    assert reason(201) == "Created"


def test_empty_statuses_drop_the_body():
    response = Response(b"ignored", 204).seal()
    assert response.body == b""
    assert may_have_body(204) is False
