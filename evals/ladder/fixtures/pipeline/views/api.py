"""JSON endpoints for the task list."""

from message.response import empty, json_response
from web.errors import BadRequest

from .store import TaskStore


def _payload(request):
    try:
        data = request.json()
    except ValueError as exc:
        raise BadRequest("body is not valid JSON: %s" % exc) from None
    if not isinstance(data, dict):
        raise BadRequest("expected a JSON object")
    return data


def register(app, store=None):
    """Attach the JSON API to ``app`` and return the backing store."""
    tasks = store if store is not None else TaskStore()

    def index(request):
        return {
            "tasks": tasks.list(state=request.arg("state"),
                                owner=request.arg("owner")),
            "counts": tasks.counts(),
        }

    def create(request):
        task = tasks.create(_payload(request))
        response = json_response(task, 201)
        response.headers.set("Location", "/api/tasks/%d" % task["id"])
        return response

    def show(request):
        return tasks.get(request.param("task_id"))

    def replace(request):
        return tasks.replace(request.param("task_id"), _payload(request))

    def destroy(request):
        tasks.remove(request.param("task_id"))
        return empty()

    app.get("/api/tasks", index, name="api.tasks.index")
    app.post("/api/tasks", create, name="api.tasks.create")
    app.get("/api/tasks/{int:task_id}", show, name="api.tasks.show")
    app.put("/api/tasks/{int:task_id}", replace, name="api.tasks.replace")
    app.delete("/api/tasks/{int:task_id}", destroy, name="api.tasks.destroy")
    return tasks
