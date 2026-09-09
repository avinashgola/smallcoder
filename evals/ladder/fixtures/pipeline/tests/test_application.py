from message.response import text_response
from middleware.builtins import ResponseHeader
from web.application import Application
from web.testing import Client
from views.site import create_app


def client():
    return Client(create_app())


def ping(request):
    return text_response("pong")


def test_home_page_renders_the_tasks():
    response = client().get("/")
    assert response.status == 200
    assert "Write the router" in response.text()


def test_api_index_reports_counts():
    payload = client().get("/api/tasks").json()
    assert payload["counts"] == {"todo": 1, "doing": 1, "done": 1}
    assert [task["id"] for task in payload["tasks"]] == [1, 2, 3]


def test_api_index_filters_by_owner():
    payload = client().get("/api/tasks", query="owner=ada").json()
    assert [task["title"] for task in payload["tasks"]] == [
        "Write the router", "Wire the chain"]


def test_creating_a_task():
    response = client().post("/api/tasks", json_body={"title": "Ship it"})
    assert response.status == 201
    assert response.headers["Location"] == "/api/tasks/4"


def test_duplicate_titles_conflict():
    response = client().post("/api/tasks", json_body={"title": "Wire the chain"})
    assert response.status == 409
    assert response.json()["code"] == "conflict"


def test_validation_errors_list_the_fields():
    response = client().post("/api/tasks", json_body={"title": "", "state": "nope"})
    assert response.status == 422
    assert sorted(response.json()["fields"]) == ["state", "title"]


def test_unknown_paths_are_json_404s():
    response = client().get("/no/such/page")
    assert response.status == 404
    assert response.json()["path"] == "/no/such/page"


def test_method_not_allowed_advertises_the_alternatives():
    response = client().delete("/api/tasks")
    assert response.status == 405
    assert response.headers["Allow"] == "GET, POST"


def test_security_headers_are_added_once():
    response = client().get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers.get_all("X-Frame-Options") == ["DENY"]


def test_request_id_flows_through_to_the_view():
    response = client().get("/whoami", headers={"X-Request-Id": "req-9"})
    assert response.text() == "req-9"


def test_non_json_bodies_are_rejected():
    response = client().post("/api/tasks", headers={"Content-Type": "text/plain"},
                             body=b"title=x")
    assert response.status == 415


def test_debug_endpoint_lists_the_installed_layers():
    labels = client().get("/_layers").json()["layers"]
    for expected in ["RequestId", "SecurityHeaders", "ErrorEnvelope", "RequireJson"]:
        assert expected in labels


def test_a_second_application_starts_with_no_middleware():
    first = Application()
    first.use(ResponseHeader("X-Leak", "yes"))
    second = Application()
    assert len(second.middleware) == 0


def test_middleware_added_to_one_application_does_not_run_in_another():
    first = Application()
    first.use(ResponseHeader("X-Leak", "yes"))
    first.get("/ping", ping)
    second = Application()
    second.get("/ping", ping)
    response = Client(second).get("/ping")
    assert response.text() == "pong"
    assert "X-Leak" not in response.headers
