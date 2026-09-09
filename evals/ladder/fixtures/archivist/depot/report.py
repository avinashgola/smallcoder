"""Rendering entries for a human reader.

Nothing here is part of the storage format - it exists so that a depot
can be printed at a terminal without the caller writing the same loop
again.  Empty values are rendered, not hidden: a note that is the empty
string and a note that was never written are different things, and a
report that showed them the same way would be lying.
"""

from .entry import Entry

EMPTY_MARK = "-"


def format_value(value):
    """Render one field value on a single line."""
    if value is None:
        return EMPTY_MARK
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return value if value else '""'
    if isinstance(value, list):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join("%s: %s" % (key, format_value(value[key])) for key in sorted(value)) + "}"
    return str(value)


def format_entry(entry, fields=None):
    """One line describing an entry."""
    if not isinstance(entry, Entry):
        raise TypeError("expected an Entry, got %r" % (entry,))
    names = sorted(entry.fields) if fields is None else list(fields)
    body = " ".join("%s=%s" % (name, format_value(entry.get(name))) for name in names)
    tags = ",".join(entry.tags.as_list()) or EMPTY_MARK
    line = "%s r%d [%s] %s" % (entry.id, entry.revision, tags, body)
    return line.rstrip()


def render_lines(entries, fields=None):
    return [format_entry(entry, fields) for entry in entries]


def field_usage(entries):
    """``field name -> how many entries carry it``."""
    usage = {}
    for entry in entries:
        for name in entry.fields:
            usage[name] = usage.get(name, 0) + 1
    return usage


def summarize(depot):
    """A small dictionary describing the whole depot."""
    entries = depot.entries()
    revisions = [entry.revision for entry in entries]
    return {
        "entries": len(entries),
        "tags": len(depot.tags()),
        "fields": len(field_usage(entries)),
        "amended": len([revision for revision in revisions if revision > 1]),
    }
