from apps.site import build_site
from kernel.testing import Client


def client():
    return Client(build_site())


def test_the_host_application_serves_its_own_routes():
    response = client().get("/health")
    assert response.status == 200
    assert response.json_body() == {"status": "ok"}


def test_the_home_page_lists_the_mount_prefixes():
    assert client().get("/").json_body()["mounts"] == ["/admin", "/api", "/docs"]


def test_the_mount_map_shows_every_application():
    tree = client().get("/_mounts").json_body()["tree"]
    assert [entry["prefix"] for entry in tree] == [
        "/", "/admin", "/api", "/api/v1", "/docs"]
    assert "/admin/users/{user_id}" in tree[1]["routes"]


def test_a_mounted_application_serves_its_index():
    response = client().get("/admin")
    assert response.status == 200
    assert response.json_body()["app"] == "admin"


def test_a_mounted_application_serves_a_path_below_it():
    response = client().get("/admin/users")
    assert response.status == 200
    assert len(response.json_body()["users"]) == 3


def test_a_mounted_application_captures_path_variables():
    response = client().get("/admin/users/2")
    assert response.status == 200
    assert response.json_body()["login"] == "grace"


def test_a_mounted_application_sees_the_outward_path():
    assert client().get("/admin/users").json_body()["here"] == "/admin/users"


def test_a_mounted_application_can_be_written_to():
    response = client().post("/admin/users", json_body={"login": "hopper"})
    assert response.status == 201
    assert response.headers["Location"] == "/admin/users/4"


def test_an_application_mounted_two_levels_deep():
    response = client().get("/api/v1/items")
    assert response.status == 200
    assert len(response.json_body()["items"]) == 3
    assert response.json_body()["here"] == "/api/v1/items"
    assert response.json_body()["self"] == "/api/v1/items"


def test_the_intermediate_application_still_serves_its_own_routes():
    assert client().get("/api/status").json_body()["versions"] == ["v1"]


def test_the_docs_application_renders_html():
    response = client().get("/docs/mounting")
    assert response.status == 200
    assert response.headers["Content-Type"].startswith("text/html")
    assert "path prefix" in response.text()


def test_an_unknown_path_below_a_mount_is_a_404():
    response = client().get("/admin/nowhere")
    assert response.status == 404
    assert response.json_body()["error"] == "not_found"


def test_an_unknown_top_level_path_is_a_404():
    assert client().get("/nowhere").status == 404


def test_a_wrong_method_on_the_host_lists_the_alternatives():
    response = client().delete("/health")
    assert response.status == 405
    assert response.headers["Allow"] == "GET, HEAD"


def test_links_built_inside_a_mounted_application_keep_the_prefix():
    body = client().get("/docs").text()
    assert 'href="/docs/mounting"' in body
