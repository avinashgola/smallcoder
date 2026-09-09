from httpkit.cookies import dump_cookie, parse_cookie_header
from httpkit.headers import Headers, parse_options, titlecase
from httpkit.query import QueryParams, parse_query_string
from httpkit.response import JsonResponse, Response, redirect
from httpkit.status import allows_body, phrase


def test_headers_are_case_insensitive():
    headers = Headers({"Content-Type": "text/plain"})
    assert headers["content-type"] == "text/plain"
    assert "CONTENT-TYPE" in headers
    headers.set("content-type", "text/html")
    assert headers.items() == [("content-type", "text/html")]


def test_headers_keep_repeated_values():
    headers = Headers()
    headers.add("Set-Cookie", "a=1")
    headers.add("Set-Cookie", "b=2")
    assert headers.get_all("set-cookie") == ["a=1", "b=2"]
    assert titlecase("set-cookie") == "Set-Cookie"


def test_parse_options():
    assert parse_options('text/html; charset="utf-8"') == (
        "text/html", {"charset": "utf-8"})


def test_query_parsing():
    params = QueryParams("tag=routing&limit=2&flag=yes&tag=intro")
    assert params.get("tag") == "routing"
    assert params.get_all("tag") == ["routing", "intro"]
    assert params.get_int("limit") == 2
    assert params.get_int("missing", 7) == 7
    assert params.get_bool("flag") is True


def test_query_percent_decoding():
    assert parse_query_string("q=a%20b+c") == [("q", "a b c")]


def test_cookies_round_trip():
    value = dump_cookie("session", "abc", max_age=60)
    assert value.startswith("session=abc; Path=/; Max-Age=60")
    assert parse_cookie_header("session=abc; theme=dark") == {
        "session": "abc", "theme": "dark"}


def test_response_defaults_and_finalize():
    response = JsonResponse({"a": 1}, 201).finalize()
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["Content-Length"] == str(len(response.body))
    assert response.text() == '{"a":1}'


def test_no_body_statuses():
    assert allows_body(204) is False
    assert phrase(204) == "No Content"
    assert Response("ignored", 204).body == b""


def test_redirect():
    response = redirect("/articles", 303)
    assert response.status == 303
    assert response.headers["Location"] == "/articles"
