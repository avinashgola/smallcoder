"""Content negotiation.

The ``offers`` a caller passes in are always listed in the server's own order
of preference, best first: when the client has no opinion, or rates several
offers equally, the earliest offer is the one that should be served.
"""

from .accept import parse_accept, parse_accept_language


def quality_of(media_type, rankings):
    """The weight the client gave ``media_type``.

    The most specific range that covers the type decides, so an explicit
    ``text/csv;q=0.2`` beats a blanket ``*/*;q=1``.
    """
    quality = 0.0
    precedence = -1
    for rank in rankings:
        if not rank.matches(media_type):
            continue
        if rank.precedence > precedence:
            precedence = rank.precedence
            quality = rank.quality
    return quality


def choose(offers, header):
    """Pick the media type to serve, or ``None`` when nothing is acceptable."""
    rankings = parse_accept(header)
    best = None
    best_quality = 0.0
    for offer in offers:
        quality = quality_of(offer, rankings)
        if quality >= best_quality:
            best = offer
            best_quality = quality
    return best


def acceptable(media_type, header):
    """Whether the client would accept ``media_type`` at all."""
    return quality_of(media_type, parse_accept(header)) > 0.0


def language_quality(tag, pairs):
    """Weight for a language tag; ``en`` also matches a request for ``en-GB``."""
    tag = tag.lower()
    quality = 0.0
    precedence = -1
    for wanted, weight in pairs:
        if wanted == "*":
            level = 0
        elif wanted == tag:
            level = 2
        elif wanted.startswith(tag + "-") or tag.startswith(wanted + "-"):
            level = 1
        else:
            continue
        if level > precedence:
            precedence = level
            quality = weight
    return quality


def choose_language(offers, header):
    """Pick a language tag, preferring the server's order on ties."""
    pairs = parse_accept_language(header)
    ranked = [(offer, language_quality(offer, pairs)) for offer in offers]
    ranked = [item for item in ranked if item[1] > 0.0]
    if not ranked:
        return None
    return max(ranked, key=lambda item: item[1])[0]
