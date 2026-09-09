"""How many people are on at each moment, and where the thin patches are."""

from shifts.clock import MINUTES_PER_DAY, format_time


def coverage_spans(assignments, day):
    """[(start minute, end minute, headcount), ...] across one calendar day."""
    day_start = day.toordinal() * MINUTES_PER_DAY
    day_end = day_start + MINUTES_PER_DAY
    edges = {day_start, day_end}
    for item in assignments:
        for edge in (item.starts_at(), item.ends_at()):
            if day_start < edge < day_end:
                edges.add(edge)
    ordered = sorted(edges)
    spans = []
    for low, high in zip(ordered, ordered[1:]):
        on_duty = sum(
            1 for item in assignments if item.starts_at() <= low and item.ends_at() >= high
        )
        spans.append((low - day_start, high - day_start, on_duty))
    return spans


def coverage_at(assignments, day, minute_of_day):
    """Headcount on duty at one moment of one day."""
    moment = day.toordinal() * MINUTES_PER_DAY + minute_of_day
    return sum(1 for item in assignments if item.starts_at() <= moment < item.ends_at())


def understaffed(assignments, day, minimum):
    """Spans of the day where fewer than *minimum* people are on duty."""
    return [
        (low, high)
        for low, high, on_duty in coverage_spans(assignments, day)
        if on_duty < minimum
    ]


def gap_report(assignments, day, minimum):
    """One '00:00-06:00 short by 1' line per thin patch."""
    lines = []
    for low, high, on_duty in coverage_spans(assignments, day):
        if on_duty < minimum:
            lines.append(
                "%s-%s short by %d"
                % (format_time(low), format_time(high), minimum - on_duty)
            )
    return lines
