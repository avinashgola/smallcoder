"""Split template source into literal text, `{{ ... }}` and `{% ... %}`."""

from collections import namedtuple

from .errors import TemplateSyntaxError

Token = namedtuple("Token", "kind value")

TEXT = "text"
VAR = "var"
TAG = "tag"

VAR_OPEN, VAR_CLOSE = "{{", "}}"
TAG_OPEN, TAG_CLOSE = "{%", "%}"


def _next_marker(source, start):
    """Offset of the next opening marker at or after `start`, or -1."""
    found = [
        offset
        for offset in (source.find(VAR_OPEN, start), source.find(TAG_OPEN, start))
        if offset != -1
    ]
    return min(found) if found else -1


def tokenize(source):
    """Return the token stream for `source`."""
    tokens = []
    pos = 0
    while pos < len(source):
        marker = _next_marker(source, pos)
        if marker == -1:
            tokens.append(Token(TEXT, source[pos:]))
            break
        if marker > pos:
            tokens.append(Token(TEXT, source[pos:marker]))
        if source.startswith(VAR_OPEN, marker):
            kind, closer = VAR, VAR_CLOSE
        else:
            kind, closer = TAG, TAG_CLOSE
        end = source.find(closer, marker + 2)
        if end == -1:
            raise TemplateSyntaxError(
                "unclosed %s starting at %r" % (kind, source[marker : marker + 16])
            )
        body = source[marker + 2 : end].strip()
        if not body:
            raise TemplateSyntaxError("empty %s block" % kind)
        tokens.append(Token(kind, body))
        pos = end + 2
    return tokens
