"""An in-memory task list."""

from web.errors import Conflict, Invalid, NotFound

STATES = ("todo", "doing", "done")


class TaskStore:
    """Tasks keyed by an integer id, handed out in creation order."""

    def __init__(self, seed=()):
        self._tasks = {}
        self._next_id = 1
        for item in seed:
            self.create(item)

    def __len__(self):
        return len(self._tasks)

    def check(self, data):
        problems = {}
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            problems["title"] = "required"
        state = data.get("state", "todo")
        if state not in STATES:
            problems["state"] = "must be one of " + ", ".join(STATES)
        owner = data.get("owner")
        if owner is not None and not isinstance(owner, str):
            problems["owner"] = "must be a string"
        extra = set(data) - {"title", "state", "owner"}
        for field in extra:
            problems[field] = "unknown field"
        if problems:
            raise Invalid(problems)
        return {"title": title.strip(), "state": state, "owner": owner}

    def create(self, data):
        clean = self.check(data)
        for task in self._tasks.values():
            if task["title"] == clean["title"]:
                raise Conflict("a task called %r already exists" % clean["title"])
        clean["id"] = self._next_id
        self._tasks[clean["id"]] = clean
        self._next_id += 1
        return clean

    def get(self, task_id):
        try:
            return self._tasks[task_id]
        except KeyError:
            raise NotFound("/tasks/%s" % task_id) from None

    def replace(self, task_id, data):
        self.get(task_id)
        clean = self.check(data)
        clean["id"] = task_id
        self._tasks[task_id] = clean
        return clean

    def remove(self, task_id):
        task = self.get(task_id)
        del self._tasks[task_id]
        return task

    def list(self, state=None, owner=None):
        tasks = [self._tasks[key] for key in sorted(self._tasks)]
        if state is not None:
            tasks = [task for task in tasks if task["state"] == state]
        if owner is not None:
            tasks = [task for task in tasks if task["owner"] == owner]
        return tasks

    def counts(self):
        return {state: len(self.list(state=state)) for state in STATES}


SEED = [
    {"title": "Write the router", "state": "done", "owner": "ada"},
    {"title": "Wire the chain", "state": "doing", "owner": "ada"},
    {"title": "Document the layers", "state": "todo", "owner": "linus"},
]
