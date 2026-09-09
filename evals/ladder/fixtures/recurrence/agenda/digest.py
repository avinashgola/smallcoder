"""Collecting, merging and grouping occurrence streams for a digest."""

from datetime import timedelta

from recur.spans import week_start
from recur.weekdays import weekday_name

SEARCH_SPAN = timedelta(days=3660)


def first_n(rule, n):
    """The first *n* occurrences of a rule, even when it is open ended."""
    taken = []
    for day in rule.occurrences(rule.start + SEARCH_SPAN):
        taken.append(day)
        if len(taken) >= n:
            break
    return taken


def count_in(rule, window_start, window_end):
    """How many occurrences land in the half-open window."""
    return len(rule.between(window_start, window_end))


def gaps(days):
    """Day counts between consecutive occurrences."""
    return [(later - earlier).days for earlier, later in zip(days, days[1:])]


def merge(rules, window_start, window_end):
    """Every (date, rule) pair from several rules, in chronological order."""
    pairs = []
    for rule in rules:
        for day in rule.between(window_start, window_end):
            pairs.append((day, rule))
    pairs.sort(key=lambda pair: pair[0])
    return pairs


def group_by_week(entries, first_weekday=0):
    """[(monday, [(date, title), ...]), ...] in chronological order."""
    buckets = {}
    for day, title in entries:
        buckets.setdefault(week_start(day, first_weekday), []).append((day, title))
    return [(key, buckets[key]) for key in sorted(buckets)]


def group_by_month(entries):
    """[(first-of-month, [(date, title), ...]), ...] in chronological order."""
    buckets = {}
    for day, title in entries:
        buckets.setdefault(day.replace(day=1), []).append((day, title))
    return [(key, buckets[key]) for key in sorted(buckets)]


def busiest_weekday(entries):
    """Weekday carrying the most entries; ties go to the earlier weekday."""
    counts = {}
    for day, _ in entries:
        counts[day.weekday()] = counts.get(day.weekday(), 0) + 1
    if not counts:
        return None
    return weekday_name(max(sorted(counts), key=lambda index: counts[index]))


def render_weekly_digest(agenda, window_start, window_end):
    """One line per week, listing the titles that fall in it."""
    lines = []
    entries = agenda.entries_between(window_start, window_end)
    for monday, rows in group_by_week(entries):
        titles = ", ".join(title for _, title in rows)
        lines.append("%s: %s" % (monday.isoformat(), titles))
    return lines
