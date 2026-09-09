from resources.site import build_server
from serve.testing import Client


def client():
    return Client(build_server())


def test_a_client_with_no_preference_gets_the_first_offer():
    response = client().get("/reports/sales")
    assert response.status == 200
    assert response.content_type.startswith("application/json")


def test_a_wildcard_accept_gets_the_first_offer():
    response = client().get("/reports/sales", headers={"Accept": "*/*"})
    assert response.content_type.startswith("application/json")


def test_an_explicit_accept_is_honoured():
    response = client().get("/reports/sales", headers={"Accept": "text/csv"})
    assert response.content_type.startswith("text/csv")
    assert response.text().splitlines()[0] == "region,quarter,units,revenue"


def test_weighted_accept_picks_the_heaviest():
    response = client().get("/reports/sales",
                            headers={"Accept": "text/csv;q=0.3, text/html;q=0.8"})
    assert response.content_type.startswith("text/html")


def test_nothing_acceptable_is_a_406():
    response = client().get("/reports/sales",
                            headers={"Accept": "application/xml"})
    assert response.status == 406
    assert response.json_body()["available"] == [
        "application/json", "text/csv", "text/html"]


def test_the_catalogue_prefers_csv():
    response = client().get("/catalog")
    assert response.content_type.startswith("text/csv")


def test_resources_advertise_what_they_vary_on():
    response = client().get("/reports/sales")
    assert response.headers["Vary"] == "Accept, Accept-Language"


def test_language_negotiation():
    response = client().get("/reports/sales", headers={"Accept-Language": "fr"})
    assert response.headers["Content-Language"] == "fr"


def test_path_variables_reach_the_resource():
    response = client().get("/reports/sales/q2", headers={"Accept": "text/csv"})
    lines = response.text().splitlines()
    assert len(lines) == 4
    assert all(",q2," in line for line in lines[1:])


def test_unknown_quarter_is_a_404():
    assert client().get("/reports/sales/q9").status == 404


def test_bad_query_argument_is_a_400():
    response = client().get("/reports/sales", query="region=west")
    assert response.status == 400
    assert response.json_body()["error"] == "bad_request"


def test_unsupported_method_lists_the_alternatives():
    response = client().delete("/catalog")
    assert response.status == 405
    assert response.headers["Allow"] == "GET"


def test_a_conditional_get_is_answered_with_304():
    session = client()
    first = session.get("/status")
    assert first.status == 200
    tag = first.headers["ETag"]
    second = session.get("/status", headers={"If-None-Match": tag})
    assert second.status == 304
    assert second.body == b""
