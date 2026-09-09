"""Parsing of the Accept family of headers."""

from wire.params import split_commas, split_params


def parse_quality(raw, default=1.0):
    """Read a ``q`` parameter, clamped to the 0..1 range."""
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value < 0:
        return 0.0
    return 1.0 if value > 1 else value


class Ranking:
    """One entry of an Accept header: a media range and its weight."""

    def __init__(self, main, sub, quality=1.0, params=None):
        self.main = main.lower()
        self.sub = sub.lower()
        self.quality = quality
        self.params = dict(params or {})

    @property
    def precedence(self):
        """How specific this range is; the most specific match wins."""
        if self.main == "*":
            return 0
        if self.sub == "*":
            return 1
        return 2 + len(self.params)

    def matches(self, media_type):
        """Whether this range covers ``media_type`` (a ``type/subtype``)."""
        if "/" not in media_type:
            return False
        main, _, sub = media_type.partition("/")
        main, sub = main.strip().lower(), sub.strip().lower()
        if self.main != "*" and self.main != main:
            return False
        if self.sub != "*" and self.sub != sub:
            return False
        return True

    def __repr__(self):
        return "<%s/%s;q=%s>" % (self.main, self.sub, self.quality)


def parse_accept(header):
    """Parse an Accept header.

    A missing or blank header means the client will take anything, so it is
    reported as a single ``*/*`` range at full quality.
    """
    rankings = []
    for chunk in split_commas(header):
        head, params = split_params(chunk)
        if "/" not in head:
            continue
        main, _, sub = head.partition("/")
        quality = parse_quality(params.pop("q", None))
        rankings.append(Ranking(main.strip(), sub.strip(), quality, params))
    if not rankings:
        return [Ranking("*", "*", 1.0)]
    return rankings


def parse_accept_language(header):
    """Parse Accept-Language into ``(tag, quality)`` pairs, blank means any."""
    pairs = []
    for chunk in split_commas(header):
        head, params = split_params(chunk)
        tag = head.strip().lower()
        if not tag:
            continue
        pairs.append((tag, parse_quality(params.get("q"))))
    if not pairs:
        return [("*", 1.0)]
    return pairs


def describe(rankings):
    """Render rankings back into a header-ish string, for debug output."""
    return ", ".join(
        "%s/%s;q=%g" % (rank.main, rank.sub, rank.quality) for rank in rankings)
