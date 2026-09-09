"""The human readable report."""

from harvester.aggregate import dropped_per_stage, slowest
from toolkit.tables import render_table
from toolkit.timing import format_duration

HEADERS = ("stage", "state", "in", "out", "time")


def render_table_for(summary):
    return render_table([outcome.as_row() for outcome in summary.recorded()], HEADERS)


def render_failures(summary):
    if not summary.failed:
        return ""
    lines = ["failures:"]
    for outcome in summary.failed:
        lines.append("  %s: %s" % (outcome.stage, outcome.error or "no detail"))
    return "\n".join(lines)


def render_hotspots(summary, count=2):
    hot = slowest(summary.recorded(), count=count)
    if not hot:
        return ""
    parts = ["%s %s" % (o.stage, format_duration(o.duration)) for o in hot]
    return "slowest: " + ", ".join(parts)


def render_drops(summary):
    drops = dropped_per_stage(summary.recorded())
    if not drops:
        return ""
    return "dropped: " + ", ".join("%s %d" % pair for pair in drops)


def render_summary(summary):
    """Full report: headline, table, then the optional detail blocks."""
    blocks = [summary.summary_line(), render_table_for(summary)]
    for block in (render_failures(summary), render_drops(summary),
                  render_hotspots(summary)):
        if block:
            blocks.append(block)
    return "\n".join(blocks)
