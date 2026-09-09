import pytest

from message.request import Request
from message.response import text_response
from middleware.base import as_layer, label_of
from middleware.builtins import (AccessLog, Cors, ErrorEnvelope, RequestId,
                                 RequireJson, ResponseHeader, SecurityHeaders,
                                 StripPrefix)
from middleware.chain import Chain
from middleware.context import context_of
from web.errors import NotFound


def endpoint(request):
    return text_response("served " + request.path)


def run(layers, request):
    return Chain(list(layers)).build(endpoint)(request)


def test_layers_run_outermost_first():
    order = []

    def outer(request, next_layer):
        order.append("outer:in")
        response = next_layer(request)
        order.append("outer:out")
        return response

    def inner(request, next_layer):
        order.append("inner")
        return next_layer(request)

    run([outer, inner], Request("GET", "/x"))
    assert order == ["outer:in", "inner", "outer:out"]


def test_chain_labels_and_copy():
    chain = Chain([ResponseHeader("X-A", "1"), SecurityHeaders()])
    assert chain.labels() == ["ResponseHeader(X-A)", "SecurityHeaders"]
    clone = chain.copy()
    clone.add(RequestId())
    assert len(chain) == 2 and len(clone) == 3


def test_only_callables_are_accepted():
    with pytest.raises(TypeError):
        Chain([]).add("not callable")
    assert label_of(as_layer(endpoint)) == "endpoint"


def test_response_header_layer():
    response = run([ResponseHeader("X-Stamp", "yes")], Request("GET", "/x"))
    assert response.headers["X-Stamp"] == "yes"


def test_security_headers_do_not_overwrite():
    def custom(request, next_layer):
        return next_layer(request).header("X-Frame-Options", "SAMEORIGIN")

    response = run([SecurityHeaders(), custom], Request("GET", "/x"))
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_request_id_is_echoed_and_published():
    seen = {}

    def peek(request, next_layer):
        seen["id"] = context_of(request).get("request_id")
        return next_layer(request)

    request = Request("GET", "/x", {"X-Request-Id": "abc123"})
    response = run([RequestId(), peek], request)
    assert seen["id"] == "abc123"
    assert response.headers["X-Request-Id"] == "abc123"


def test_error_envelope_renders_http_errors():
    def boom(request):
        raise NotFound("/gone")

    response = Chain([ErrorEnvelope()]).build(boom)(Request("GET", "/gone"))
    assert response.status == 404
    assert response.json()["code"] == "not_found"


def test_require_json_rejects_other_media_types():
    request = Request("POST", "/x", {"Content-Type": "text/plain"}, body=b"hi")
    response = run([ErrorEnvelope(), RequireJson()], request)
    assert response.status == 415


def test_strip_prefix_rewrites_the_path():
    response = run([StripPrefix("/svc")], Request("GET", "/svc/tasks"))
    assert response.text() == "served /tasks"
    response = run([StripPrefix("/svc")], Request("GET", "/svc"))
    assert response.text() == "served /"


def test_cors_preflight():
    request = Request("OPTIONS", "/x", {
        "Origin": "https://example.test",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    response = run([Cors(["https://example.test"], ("GET", "POST"))], request)
    assert response.status == 204
    assert response.headers["Access-Control-Allow-Origin"] == "https://example.test"
    assert response.headers["Access-Control-Allow-Headers"] == "content-type"


def test_access_log_records_one_line_per_request():
    sink = []
    run([AccessLog(sink)], Request("GET", "/x"))
    run([AccessLog(sink)], Request("POST", "/y"))
    assert sink == ["GET /x -> 200", "POST /y -> 200"]
