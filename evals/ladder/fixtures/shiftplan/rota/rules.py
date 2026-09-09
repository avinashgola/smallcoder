"""Working time rules, and the violations a rota breaks."""

from rota.assignments import by_person

DEFAULT_MIN_REST_MINUTES = 11 * 60
DEFAULT_MAX_CONSECUTIVE_DAYS = 6
DEFAULT_MAX_WEEKLY_MINUTES = 48 * 60


class Policy(object):
    """The working time limits a rota is checked against."""

    def __init__(
        self,
        min_rest_minutes=DEFAULT_MIN_REST_MINUTES,
        max_consecutive_days=DEFAULT_MAX_CONSECUTIVE_DAYS,
        max_weekly_minutes=DEFAULT_MAX_WEEKLY_MINUTES,
    ):
        self.min_rest_minutes = min_rest_minutes
        self.max_consecutive_days = max_consecutive_days
        self.max_weekly_minutes = max_weekly_minutes


def days_worked(shifts):
    """The distinct calendar days a person is rostered on, in order."""
    return sorted({shift.day for shift in shifts})


def longest_streak(days):
    """Length of the longest run of consecutive days in an ordered list."""
    if not days:
        return 0
    best = 1
    run = 1
    for previous, current in zip(days, days[1:]):
        if (current - previous).days == 1:
            run += 1
            if run > best:
                best = run
        else:
            return best
    return best


def rest_gaps(shifts):
    """[(earlier shift, later shift, minutes between them), ...]."""
    ordered = sorted(shifts, key=lambda shift: shift.starts_at())
    return [
        (earlier, later, later.starts_at() - earlier.ends_at())
        for earlier, later in zip(ordered, ordered[1:])
    ]


def weekly_minutes(shifts):
    """[(ISO week label, minutes rostered), ...], counted against the start day."""
    totals = {}
    for shift in shifts:
        year, week, _ = shift.day.isocalendar()
        label = "%d-W%02d" % (year, week)
        totals[label] = totals.get(label, 0) + shift.duration()
    return [(label, totals[label]) for label in sorted(totals)]


def consecutive_days(assignments):
    """[(person, longest run of consecutive days rostered), ...] by name."""
    return [
        (person, longest_streak(days_worked(shifts)))
        for person, shifts in by_person(assignments)
    ]


def violations(assignments, policy=None):
    """Every working time rule the rota breaks, grouped by person."""
    limits = policy or Policy()
    found = []
    for person, shifts in by_person(assignments):
        for earlier, later, gap in rest_gaps(shifts):
            if gap < limits.min_rest_minutes:
                found.append(
                    "%s: %d minutes rest between %s and %s (minimum %d)"
                    % (person, gap, earlier.day, later.day, limits.min_rest_minutes)
                )
        streak = longest_streak(days_worked(shifts))
        if streak > limits.max_consecutive_days:
            found.append(
                "%s: %d consecutive days rostered (maximum %d)"
                % (person, streak, limits.max_consecutive_days)
            )
        for label, minutes in weekly_minutes(shifts):
            if minutes > limits.max_weekly_minutes:
                found.append(
                    "%s: %d minutes in %s (maximum %d)"
                    % (person, minutes, label, limits.max_weekly_minutes)
                )
    return found
