"""The admin application, normally served under a prefix."""

from kernel.application import Application
from kernel.errors import Invalid, NotFound
from kernel.views import MethodView
from net.response import json_response

from .data import USERS, user_by_id, users_with_role


def _user_id(request):
    raw = request.var("user_id", "")
    if not raw.isdigit():
        raise NotFound(request.full_path)
    return int(raw)


class UserCollection(MethodView):
    """The user collection: list the users, or add one."""

    def get(self, request):
        role = request.arg("role")
        rows = users_with_role(role) if role else [dict(u) for u in USERS]
        return {"users": rows, "here": request.full_path}

    def post(self, request):
        payload = request.json() or {}
        problems = {}
        if not payload.get("login"):
            problems["login"] = "required"
        elif any(user["login"] == payload["login"] for user in USERS):
            problems["login"] = "taken"
        if problems:
            raise Invalid(problems)
        created = {"id": max(user["id"] for user in USERS) + 1,
                   "login": payload["login"],
                   "roles": list(payload.get("roles", [])),
                   "active": True}
        response = json_response(created, 201)
        response.headers.assign("Location",
                                request.full_path + "/%d" % created["id"])
        return response


def build_admin(settings=None):
    """The admin application, ready to be mounted anywhere."""
    app = Application("admin", settings)

    def index(request):
        return {"app": "admin", "users": len(USERS), "here": request.full_path}

    def user_detail(request):
        user = user_by_id(_user_id(request))
        if user is None:
            raise NotFound(request.full_path)
        return user

    def user_roles(request):
        user = user_by_id(_user_id(request))
        if user is None:
            raise NotFound(request.full_path)
        return {"login": user["login"], "roles": user["roles"]}

    app.get("/", index, name="admin.index")
    UserCollection.attach(app, "/users", name="admin.users")
    app.get("/users/{user_id}", user_detail, name="admin.user")
    app.get("/users/{user_id}/roles", user_roles, name="admin.user.roles")
    return app
