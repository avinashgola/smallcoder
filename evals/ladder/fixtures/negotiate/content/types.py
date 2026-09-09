"""Media type helpers, kept deliberately functional."""

from wire.params import join_params, split_params

JSON = "application/json"
CSV = "text/csv"
HTML = "text/html"
TEXT = "text/plain"

EXTENSIONS = {
    JSON: "json",
    CSV: "csv",
    HTML: "html",
    TEXT: "txt",
}

TEXTUAL = frozenset([CSV, HTML, TEXT, JSON, "application/xml"])


def parse_type(value):
    """``('text', 'csv', {'charset': 'utf-8'})`` or ``None`` if unparsable."""
    if not value or not value.strip():
        return None
    head, params = split_params(value)
    if "/" not in head:
        return None
    main, _, sub = head.partition("/")
    main, sub = main.strip().lower(), sub.strip().lower()
    if not main or not sub:
        return None
    return main, sub, params


def essence(value):
    """Just the ``type/subtype`` part, lower-cased."""
    parsed = parse_type(value)
    return None if parsed is None else "%s/%s" % (parsed[0], parsed[1])


def format_type(main, sub, params=None):
    return join_params("%s/%s" % (main, sub), params or {})


def is_textual(media_type):
    return essence(media_type) in TEXTUAL


def extension_for(media_type):
    return EXTENSIONS.get(essence(media_type), "bin")


def with_charset(media_type, charset):
    """Attach a charset parameter to a textual media type."""
    parsed = parse_type(media_type)
    if parsed is None:
        return media_type
    main, sub, params = parsed
    if not is_textual(media_type):
        return format_type(main, sub, params)
    params = dict(params)
    params.setdefault("charset", charset)
    return format_type(main, sub, params)
