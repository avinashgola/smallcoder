"""Walk a parsed template and produce the rendered string."""

from .errors import UndefinedVariable, UnknownFilter

QUOTES = "'\""


def lookup(context, path):
    """Resolve a dotted path such as `user.name` against `context`."""
    value = context
    for part in path.split("."):
        if isinstance(value, dict):
            if part not in value:
                raise UndefinedVariable(path)
            value = value[part]
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            raise UndefinedVariable(path)
    return value


def stringify(value):
    """Render a Python value the way a template should show it."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def _resolve(token, context):
    """A quoted literal, or a lookup into the context."""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in QUOTES:
        return token[1:-1]
    return lookup(context, token)


def evaluate(expression, context, filters):
    """Evaluate `name|filter|filter` against the context."""
    parts = [part.strip() for part in expression.split("|")]
    value = _resolve(parts[0], context)
    for name in parts[1:]:
        if name not in filters:
            raise UnknownFilter(name)
        value = filters[name](value)
    return value


def render_nodes(nodes, context, filters):
    """Render a node list, returning the concatenated output."""
    out = []
    for node in nodes:
        kind = node[0]
        if kind == "text":
            out.append(node[1])
        elif kind == "var":
            out.append(stringify(evaluate(node[1], context, filters)))
        elif kind == "if":
            taken = node[2] if evaluate(node[1], context, filters) else node[3]
            out.append(render_nodes(taken, context, filters))
        else:
            name, expression, body = node[1], node[2], node[3]
            scope = dict(context)
            for item in evaluate(expression, context, filters):
                scope[name] = item
                out.append(render_nodes(body, scope, filters))
    return "".join(out)
