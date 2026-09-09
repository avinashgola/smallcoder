"""Compiled URL templates such as ``/users/{user_id}/posts``.

A template is compiled into the literal text around its placeholders and
matched against the path from the very first character, so the paths handed
to it have to be absolute: ``users/7`` does not match ``/users/{user_id}``.
"""


class TemplateError(ValueError):
    """Raised for a template that cannot be compiled."""


def compile_template(source):
    """Return ``(literals, names)`` for ``source``.

    ``literals`` always has exactly one more element than ``names``: the text
    before the first placeholder, between each pair, and after the last one.
    """
    literals = []
    names = []
    buffer = []
    index = 0
    while index < len(source):
        char = source[index]
        if char == "{":
            end = source.find("}", index)
            if end == -1:
                raise TemplateError("unclosed placeholder in %r" % (source,))
            name = source[index + 1:end].strip()
            if not name:
                raise TemplateError("unnamed placeholder in %r" % (source,))
            if name in names:
                raise TemplateError("duplicate placeholder %r" % (name,))
            literals.append("".join(buffer))
            names.append(name)
            buffer = []
            index = end + 1
            continue
        if char == "}":
            raise TemplateError("stray '}' in %r" % (source,))
        buffer.append(char)
        index += 1
    literals.append("".join(buffer))
    return literals, names


class Template:
    """One compiled template."""

    def __init__(self, source):
        if not source.startswith("/"):
            raise TemplateError("templates are absolute: %r" % (source,))
        self.source = source if source == "/" else source.rstrip("/")
        self.literals, self.names = compile_template(self.source)

    @property
    def is_static(self):
        return not self.names

    def match(self, path):
        """Captured placeholder values, or ``None`` when ``path`` differs.

        Matching starts at the first character of ``path``; a path that does
        not begin with the template's leading literal never matches.
        """
        head = self.literals[0]
        if not path.startswith(head):
            return None
        cursor = len(head)
        captured = {}
        for index, name in enumerate(self.names):
            tail = self.literals[index + 1]
            if tail:
                stop = path.find(tail, cursor)
                if stop == -1:
                    return None
            else:
                stop = len(path)
            chunk = path[cursor:stop]
            if not chunk or "/" in chunk:
                return None
            captured[name] = chunk
            cursor = stop + len(tail)
        if cursor != len(path):
            return None
        return captured

    def build(self, values):
        """Fill the template in, the inverse of :meth:`match`."""
        out = [self.literals[0]]
        for index, name in enumerate(self.names):
            if name not in values:
                raise KeyError("missing %r for %r" % (name, self.source))
            out.append(str(values[name]))
            out.append(self.literals[index + 1])
        return "".join(out)

    def __repr__(self):
        return "Template(%r)" % (self.source,)
