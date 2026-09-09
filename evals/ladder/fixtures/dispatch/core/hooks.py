"""Before- and after-request hooks.

Hooks are deliberately simpler than middleware: a before-hook may short
circuit the request by returning something, an after-hook only decorates the
response that has already been produced.
"""


class HookRegistry:
    """Ordered collections of before/after callables."""

    def __init__(self):
        self.before = []
        self.after = []
        self.teardown = []

    def add_before(self, func):
        self.before.append(func)
        return func

    def add_after(self, func):
        self.after.append(func)
        return func

    def add_teardown(self, func):
        self.teardown.append(func)
        return func

    def run_before(self, request):
        """Return the first non-``None`` result, if any hook short circuits."""
        for hook in self.before:
            result = hook(request)
            if result is not None:
                return result
        return None

    def run_after(self, request, response):
        for hook in self.after:
            replacement = hook(request, response)
            if replacement is not None:
                response = replacement
        return response

    def run_teardown(self, request, error=None):
        for hook in self.teardown:
            hook(request, error)

    def __len__(self):
        return len(self.before) + len(self.after) + len(self.teardown)
