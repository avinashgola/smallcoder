from wire.etag import etag_for, tag_matches
from wire.headers import Headers, vary
from wire.params import join_params, split_commas, split_params
from wire.request import Request
from wire.response import Response
from wire.status import NOT_ACCEPTABLE, bodyless, reason
from wire.urls import parts, percent_decode, query_pairs, tidy


def test_headers_lookup_ignores_case():
    headers = Headers({"Content-Type": "text/csv"})
    assert headers["content-type"] == "text/csv"
    assert headers.first("CONTENT-TYPE") == "text/csv"
    assert "content-type" in headers


def test_headers_keep_repeats_and_list_values():
    headers = Headers()
    headers.append("Vary", "Accept")
    headers.append("Vary", "Accept-Language, Origin")
    assert headers.every("vary") == ["Accept", "Accept-Language, Origin"]
    assert headers.listed("vary") == ["Accept", "Accept-Language", "Origin"]


def test_vary_does_not_duplicate():
    headers = Headers({"Vary": "Accept"})
    vary(headers, "Accept", "Accept-Language")
    assert headers["Vary"] == "Accept, Accept-Language"


def test_split_commas_respects_quotes():
    assert split_commas('a/b;x="1,2", c/d') == ['a/b;x="1,2"', "c/d"]


def test_split_and_join_params():
    head, params = split_params('text/csv; charset=utf-8; header="present"')
    assert head == "text/csv"
    assert params == {"charset": "utf-8", "header": "present"}
    assert join_params(head, params) == "text/csv; charset=utf-8; header=present"


def test_url_helpers():
    assert tidy("reports//sales/") == "/reports/sales"
    assert parts("/a/b") == ["a", "b"]
    assert query_pairs("?region=north&q=a%2Fb") == [("region", "north"), ("q", "a/b")]
    assert percent_decode("a+b") == "a b"


def test_request_reads_its_headers():
    request = Request("get", "/x", {"Accept": "text/csv",
                                    "Content-Type": "application/json; charset=ascii"},
                      "region=north", b'{"a": 1}')
    assert request.method == "GET"
    assert request.accept() == "text/csv"
    assert request.content_type() == "application/json"
    assert request.charset() == "ascii"
    assert request.arg("region") == "north"
    assert request.json() == {"a": 1}


def test_response_close_sets_length():
    response = Response("hello", content_type="text/plain").close()
    assert response.headers["Content-Length"] == "5"
    assert response.content_type == "text/plain"


def test_bodyless_statuses():
    assert bodyless(204) is True
    assert reason(NOT_ACCEPTABLE) == "Not Acceptable"


def test_etags_are_stable_and_comparable():
    tag = etag_for(b"payload")
    assert tag == etag_for(b"payload")
    assert tag != etag_for(b"other")
    assert tag_matches(tag, 'W/%s, "zzz"' % tag) is True
    assert tag_matches(tag, "*") is True
    assert tag_matches(tag, None) is False
