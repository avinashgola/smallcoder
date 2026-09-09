"""Parsing of ``type/subtype; parameter=value`` header values."""


class MediaType:
    """One parsed media type plus its parameters."""

    def __init__(self, main, sub, params=None):
        self.main = main.lower()
        self.sub = sub.lower()
        self.params = dict(params or {})

    @property
    def essence(self):
        return "%s/%s" % (self.main, self.sub)

    @property
    def charset(self):
        return self.params.get("charset")

    def matches(self, other):
        """Wildcard-aware comparison against another media type."""
        if isinstance(other, str):
            other = parse_media_type(other)
        if other is None:
            return False
        main_ok = self.main == "*" or other.main == "*" or self.main == other.main
        sub_ok = self.sub == "*" or other.sub == "*" or self.sub == other.sub
        return main_ok and sub_ok

    def with_charset(self, charset):
        params = dict(self.params)
        params["charset"] = charset
        return MediaType(self.main, self.sub, params)

    def __str__(self):
        parts = [self.essence]
        for key in sorted(self.params):
            parts.append("%s=%s" % (key, self.params[key]))
        return "; ".join(parts)

    def __eq__(self, other):
        if isinstance(other, str):
            other = parse_media_type(other)
        return (isinstance(other, MediaType) and self.essence == other.essence
                and self.params == other.params)

    def __repr__(self):
        return "MediaType(%r)" % (str(self),)


def parse_media_type(value):
    """Parse one media type, returning ``None`` for blank input."""
    if not value or not value.strip():
        return None
    chunks = value.split(";")
    essence = chunks[0].strip()
    if "/" not in essence:
        return None
    main, _, sub = essence.partition("/")
    params = {}
    for chunk in chunks[1:]:
        if "=" not in chunk:
            continue
        key, _, raw = chunk.partition("=")
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            raw = raw[1:-1]
        params[key.strip().lower()] = raw
    return MediaType(main.strip(), sub.strip(), params)


JSON = MediaType("application", "json")
TEXT = MediaType("text", "plain", {"charset": "utf-8"})
HTML = MediaType("text", "html", {"charset": "utf-8"})
