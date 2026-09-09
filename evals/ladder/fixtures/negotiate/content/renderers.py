"""Renderers turn a view's data into bytes for one media type."""

import json

from .charset import DEFAULT, encode
from .types import CSV, HTML, JSON, TEXT, with_charset


def escape(text):
    """Escape the five characters that matter inside HTML markup."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def quote_cell(value):
    """Quote one CSV field the way RFC 4180 asks for."""
    text = "" if value is None else str(value)
    if any(char in text for char in ',"\n\r'):
        return '"%s"' % text.replace('"', '""')
    return text


def columns_of(rows):
    """Column names in first-seen order across every row."""
    names = []
    for row in rows:
        for key in row:
            if key not in names:
                names.append(key)
    return names


class Renderer:
    """Base class: a media type plus a way of turning data into text."""

    media_type = TEXT

    def render(self, data):
        raise NotImplementedError

    def content_type(self, charset=DEFAULT):
        return with_charset(self.media_type, charset)

    def encode(self, data, charset=DEFAULT):
        return encode(self.render(data), charset)

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.media_type)


class JsonRenderer(Renderer):
    media_type = JSON

    def __init__(self, indent=None):
        self.indent = indent

    def render(self, data):
        separators = (",", ":") if self.indent is None else None
        return json.dumps(data, sort_keys=True, indent=self.indent,
                          separators=separators)


class CsvRenderer(Renderer):
    """Renders a list of dicts, or a dict whose ``rows`` key holds one."""

    media_type = CSV

    def __init__(self, columns=None):
        self.columns = list(columns) if columns else None

    def rows_of(self, data):
        if isinstance(data, dict):
            data = data.get("rows", [])
        if not isinstance(data, list):
            raise TypeError("csv needs a list of rows")
        return [row for row in data if isinstance(row, dict)]

    def render(self, data):
        rows = self.rows_of(data)
        columns = self.columns or columns_of(rows)
        lines = [",".join(quote_cell(name) for name in columns)]
        for row in rows:
            lines.append(",".join(quote_cell(row.get(name)) for name in columns))
        return "\r\n".join(lines) + "\r\n"


class HtmlRenderer(Renderer):
    """Renders a table, with the document title taken from the data."""

    media_type = HTML

    def __init__(self, title="Report"):
        self.title = title

    def render(self, data):
        rows = data.get("rows", []) if isinstance(data, dict) else data
        title = data.get("title", self.title) if isinstance(data, dict) else self.title
        columns = columns_of(rows)
        head = "".join("<th>%s</th>" % escape(name) for name in columns)
        body = []
        for row in rows:
            cells = "".join("<td>%s</td>" % escape(row.get(name, ""))
                            for name in columns)
            body.append("<tr>%s</tr>" % cells)
        return ("<!doctype html><html><head><title>%s</title></head>"
                "<body><h1>%s</h1><table><thead><tr>%s</tr></thead>"
                "<tbody>%s</tbody></table></body></html>"
                % (escape(title), escape(title), head, "".join(body)))


class TextRenderer(Renderer):
    """A plain listing, one ``key: value`` pair per line."""

    media_type = TEXT

    def render(self, data):
        if isinstance(data, dict) and "rows" in data:
            data = data["rows"]
        if isinstance(data, list):
            blocks = []
            for row in data:
                blocks.append("\n".join("%s: %s" % (key, row[key])
                                        for key in sorted(row)))
            return "\n\n".join(blocks) + "\n"
        if isinstance(data, dict):
            return "\n".join("%s: %s" % (key, data[key])
                             for key in sorted(data)) + "\n"
        return str(data) + "\n"


REGISTRY = {
    JSON: JsonRenderer(),
    CSV: CsvRenderer(),
    HTML: HtmlRenderer(),
    TEXT: TextRenderer(),
}


def renderer_for(media_type):
    """The renderer registered for a media type."""
    try:
        return REGISTRY[media_type]
    except KeyError:
        raise KeyError("no renderer for %r" % (media_type,)) from None


def supported_types():
    """Every media type the server can produce, in registration order."""
    return list(REGISTRY)
