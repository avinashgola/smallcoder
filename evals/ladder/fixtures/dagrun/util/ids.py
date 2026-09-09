"""Identifier helpers for job and run names.

Job ids are user supplied, so they get normalised once on the way in and are
treated as opaque strings everywhere else.
"""

ALLOWED_EXTRA = "-_."


def normalize_id(raw):
    """Lowercase and trim an id, rejecting anything that is not usable."""
    if not isinstance(raw, str):
        raise ValueError("job id must be a string, got %r" % (raw,))
    text = raw.strip().lower()
    if not text:
        raise ValueError("job id must not be empty")
    for ch in text:
        if not (ch.isalnum() or ch in ALLOWED_EXTRA):
            raise ValueError("job id %r contains an illegal character %r" % (raw, ch))
    return text


def is_group_ref(raw):
    """True when a dependency entry points at a group rather than a job."""
    return isinstance(raw, str) and raw.strip().startswith("@")


def group_name(raw):
    """Strip the '@' marker off a group reference."""
    text = raw.strip()
    if not text.startswith("@"):
        raise ValueError("%r is not a group reference" % (raw,))
    return normalize_id(text[1:])


def run_id(prefix, counter):
    """Deterministic run identifier; the counter is supplied by the caller."""
    return "%s-%04d" % (normalize_id(prefix), counter)


def short(job_id, width=12):
    """Shorten an id for table output without losing the tail."""
    if len(job_id) <= width:
        return job_id
    if width <= 3:
        return job_id[:width]
    keep = width - 3
    head = (keep + 1) // 2
    tail = keep - head
    return job_id[:head] + "..." + (job_id[-tail:] if tail else "")
