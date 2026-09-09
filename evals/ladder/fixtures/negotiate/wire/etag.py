"""Entity tags and the conditional-GET comparison they feed."""

import hashlib


def etag_for(body, weak=False):
    """A stable entity tag derived from the response body."""
    digest = hashlib.sha1(body).hexdigest()[:16]
    return ('W/"%s"' if weak else '"%s"') % digest


def strip_weakness(tag):
    tag = tag.strip()
    return tag[2:] if tag.startswith("W/") else tag


def parse_tag_list(header):
    """Split an If-None-Match style header into individual tags."""
    if not header:
        return []
    return [tag.strip() for tag in header.split(",") if tag.strip()]


def tag_matches(etag, header):
    """Whether ``etag`` is covered by the tags a client sent."""
    tags = parse_tag_list(header)
    if not tags:
        return False
    if "*" in tags:
        return True
    wanted = strip_weakness(etag)
    return any(strip_weakness(tag) == wanted for tag in tags)
