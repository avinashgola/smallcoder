"""Cookie header parsing and Set-Cookie construction."""

SAME_SITE_VALUES = ("Strict", "Lax", "None")


def parse_cookie_header(value):
    """Parse a ``Cookie:`` header into a plain dict."""
    jar = {}
    if not value:
        return jar
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        name, _, raw = chunk.partition("=")
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            raw = raw[1:-1]
        jar[name.strip()] = raw
    return jar


def dump_cookie(name, value, path="/", domain=None, max_age=None,
                secure=False, http_only=True, same_site="Lax"):
    """Build the value half of a ``Set-Cookie`` header."""
    if same_site not in SAME_SITE_VALUES:
        raise ValueError("bad SameSite value: %r" % (same_site,))
    if same_site == "None" and not secure:
        raise ValueError("SameSite=None requires Secure")
    parts = ["%s=%s" % (name, value)]
    if path:
        parts.append("Path=%s" % path)
    if domain:
        parts.append("Domain=%s" % domain)
    if max_age is not None:
        parts.append("Max-Age=%d" % int(max_age))
    if secure:
        parts.append("Secure")
    if http_only:
        parts.append("HttpOnly")
    parts.append("SameSite=%s" % same_site)
    return "; ".join(parts)


def expire_cookie(name, path="/"):
    """A ``Set-Cookie`` value that deletes ``name`` on the client."""
    return dump_cookie(name, "", path=path, max_age=0)
