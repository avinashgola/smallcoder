import pytest

from kernel.errors import MethodNotAllowed, NotFound
from mounting.prefix import covers, depth, join, normalize_prefix
from mounting.table import MountTable
from routes.router import Router
from routes.template import Template, TemplateError, compile_template
from routes.urls import encode_query, path_of, quote, url_for


def handler(request):
    return "ok"


def test_compile_template_splits_literals_and_names():
    literals, names = compile_template("/users/{user_id}/roles")
    assert literals == ["/users/", "/roles"]
    assert names == ["user_id"]


def test_bad_templates_are_rejected():
    with pytest.raises(TemplateError):
        Template("users/{id}")
    with pytest.raises(TemplateError):
        Template("/users/{id")
    with pytest.raises(TemplateError):
        Template("/users/{}")


def test_static_template_matches_exactly():
    template = Template("/users")
    assert template.match("/users") == {}
    assert template.match("/users/1") is None
    assert template.is_static


def test_template_captures_one_segment():
    template = Template("/users/{user_id}")
    assert template.match("/users/7") == {"user_id": "7"}
    assert template.match("/users/7/roles") is None
    assert template.match("/users/") is None


def test_template_matching_starts_at_the_first_character():
    template = Template("/users/{user_id}")
    assert template.match("users/7") is None
    assert template.match("/admin/users/7") is None


def test_root_template():
    assert Template("/").match("/") == {}
    assert Template("/").match("") is None


def test_template_build_is_the_inverse_of_match():
    template = Template("/users/{user_id}/roles")
    assert template.build({"user_id": 3}) == "/users/3/roles"
    with pytest.raises(KeyError):
        template.build({})


def test_router_returns_the_first_match():
    router = Router()
    router.add("/users/me", handler, name="me")
    router.add("/users/{user_id}", handler, name="one")
    route, captured = router.find("GET", "/users/me")
    assert route.name == "me"
    assert captured == {}


def test_router_reports_missing_and_wrong_methods():
    router = Router()
    router.add("/users", handler, ("GET",))
    with pytest.raises(NotFound):
        router.find("GET", "/nope")
    with pytest.raises(MethodNotAllowed):
        router.find("DELETE", "/users")


def test_prefix_helpers():
    assert normalize_prefix("admin/") == "/admin"
    assert normalize_prefix("/") == ""
    assert covers("/admin/users", "/admin")
    assert not covers("/administration", "/admin")
    assert covers("/anything", "")
    assert join("/admin", "/users") == "/admin/users"
    assert join("/admin", "/") == "/admin"
    assert depth("/api/v1") == 2


def test_mount_table_orders_by_prefix_length():
    table = MountTable()
    table.add("/api", object(), name="api")
    table.add("/api/v1", object(), name="v1")
    assert [mount.name for mount in table.ordered()] == ["v1", "api"]


def test_a_prefix_can_only_be_mounted_once():
    table = MountTable()
    table.add("/admin", object(), name="admin")
    with pytest.raises(ValueError):
        table.add("/admin/", object(), name="again")


def test_a_root_mount_sees_the_path_unchanged():
    table = MountTable()
    table.add("/", object(), name="root")
    mount, inner = table.resolve("/anything/at/all")
    assert mount.name == "root"
    assert inner == "/anything/at/all"


def test_resolve_returns_none_when_nothing_is_mounted():
    assert MountTable().resolve("/admin") is None


class _App:
    """Just enough of an application for the URL builder."""

    def __init__(self):
        self.router = Router()


def test_url_for_puts_the_prefix_back_on():
    app = _App()
    app.router.add("/users/{user_id}", handler, name="admin.user")
    assert url_for(app, "admin.user", {"user_id": 4}) == "/users/4"
    assert url_for(app, "admin.user", {"user_id": 4},
                   script_name="/admin") == "/admin/users/4"
    assert path_of(app, "admin.user", {"user_id": 4}) == "/users/4"


def test_url_for_encodes_the_query():
    app = _App()
    app.router.add("/search", handler, name="search")
    assert url_for(app, "search", query={"q": "two words"}) == "/search?q=two%20words"
    assert encode_query(None) == ""
    assert quote("a/b") == "a%2Fb"
