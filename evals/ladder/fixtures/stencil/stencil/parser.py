"""Turn a token stream into a tree of nodes.

Nodes are plain tuples so the renderer can dispatch on `node[0]`:
    ("text", literal)
    ("var", expression)
    ("if", expression, body, alternative)
    ("for", name, expression, body)
"""

from .errors import TemplateSyntaxError
from .lexer import TEXT, VAR, tokenize


def parse(source):
    """Compile `source` into a list of nodes."""
    tokens = tokenize(source)
    nodes, index = _parse_block(tokens, 0, ())
    if index != len(tokens):
        raise TemplateSyntaxError("unexpected tag %r" % tokens[index].value)
    return nodes


def _parse_block(tokens, index, stoppers):
    """Parse until one of `stoppers` is reached; the stopper is not consumed."""
    nodes = []
    while index < len(tokens):
        token = tokens[index]
        if token.kind == TEXT:
            nodes.append(("text", token.value))
            index += 1
        elif token.kind == VAR:
            nodes.append(("var", token.value))
            index += 1
        elif token.value.split()[0] in stoppers:
            return nodes, index
        else:
            index = _parse_tag(tokens, index, nodes)
    if stoppers:
        raise TemplateSyntaxError("missing %s" % " or ".join(sorted(stoppers)))
    return nodes, index


def _parse_tag(tokens, index, nodes):
    """Parse one block tag, appending its node; returns the next index."""
    parts = tokens[index].value.split()
    keyword = parts[0]
    if keyword == "if":
        if len(parts) != 2:
            raise TemplateSyntaxError("if takes exactly one expression")
        body, index = _parse_block(tokens, index + 1, ("else", "endif"))
        alternative = []
        if tokens[index].value.split()[0] == "else":
            alternative, index = _parse_block(tokens, index + 1, ("endif",))
        nodes.append(("if", parts[1], body, alternative))
        return index + 1
    if keyword == "for":
        if len(parts) != 4 or parts[2] != "in":
            raise TemplateSyntaxError("for takes 'NAME in EXPRESSION'")
        body, index = _parse_block(tokens, index + 1, ("endfor",))
        nodes.append(("for", parts[1], parts[3], body))
        return index + 1
    raise TemplateSyntaxError("unknown tag %r" % keyword)
