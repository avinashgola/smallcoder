import pytest

from net.headers import Headers
from net.request import Request, clean, parse_query
from net.response import Response, json_response, redirect
from net.status import has_body, reason
from kernel.errors import MethodNotAllowed
from kernel.views import MethodView


def test_headers_are_case_insensitive():
    headers = Headers({"Content-Type": "text/plain"})
    assert headers["content-type"] == "text/plain"
    assert "CONTENT-TYPE" in headers
    headers.assign("content-type", "text/html")
    assert headers.items() == [("content-type", "text/html")]


def test_headers_keep_repeats():
    headers = Headers()
    headers.append("Set-Cookie", "a=1")
    headers.append("Set-Cookie", "b=2")
    assert headers.all("set-cookie") == ["a=1", "b=2"]
    assert len(headers) == 2


def test_headers_fallback_does_not_overwrite():
    headers = Headers({"Server": "custom"})
    headers.fallback("Server", "default")
    assert headers["Server"] == "custom"


def test_clean_leaves_relative_paths_relative():
    assert clean("/a//b/") == "/a/b"
    assert clean("/") == "/"
    assert clean("a/b") == "a/b"


def test_query_parsing():
    assert parse_query("?role=admin&q=two+words") == [
        ("role", "admin"), ("q", "two words")]


def test_request_arguments_and_body():
    request = Request("post", "/users", None, "role=admin", b'{"login":"ada"}')
    assert request.method == "POST"
    assert request.arg("role") == "admin"
    assert request.arg("missing", "none") == "none"
    assert request.json() == {"login": "ada"}


def test_relocate_records_the_consumed_prefix():
    request = Request("GET", "/admin/users")
    inner = request.relocate("/users", "/admin")
    assert inner.path == "/users"
    assert inner.script_name == "/admin"
    assert inner.full_path == "/admin/users"
    assert request.full_path == "/admin/users"


def test_relocate_shares_the_notes():
    request = Request("GET", "/admin/users")
    request.notes["seen"] = True
    assert request.relocate("/users", "/admin").notes["seen"] is True


def test_response_finish_sets_length():
    response = json_response({"a": 1}).finish()
    assert response.headers["Content-Length"] == "7"
    assert response.json_body() == {"a": 1}


def test_empty_statuses_drop_the_body():
    response = Response(b"ignored", 204).finish()
    assert response.body == b""
    assert has_body(204) is False
    assert reason(204) == "No Content"


def test_redirect_needs_a_redirect_status():
    assert redirect("/elsewhere", 308).headers["Location"] == "/elsewhere"
    with pytest.raises(ValueError):
        redirect("/elsewhere", 200)


class _Greeting(MethodView):
    def get(self, request):
        return "hello"

    def post(self, request):
        return ("made", 201)


def test_method_view_dispatches_on_the_verb():
    view = _Greeting()
    assert view.allowed() == ["GET", "POST"]
    assert view(Request("GET", "/greet")) == "hello"
    assert view(Request("HEAD", "/greet")) == "hello"
    assert view(Request("POST", "/greet")) == ("made", 201)


def test_method_view_rejects_verbs_it_does_not_implement():
    with pytest.raises(MethodNotAllowed):
        _Greeting()(Request("DELETE", "/greet"))
