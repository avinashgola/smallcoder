"""Who is on which shift, and the clashes that creates."""

from datetime import date

from shifts.clock import MINUTES_PER_DAY
from shifts.templates import UnknownShift, template
from shifts.window import Window

FIELD_COUNT = 3


class RotaError(ValueError):
    """Raised when a rota line cannot be read."""


class Assignment(object):
    """One person on one shift on one calendar day."""

    def __init__(self, person, day, shift):
        if isinstance(shift, Window):
            self.name = shift.text()
            self.window = shift
        else:
            self.name = str(shift).strip().lower()
            self.window = template(self.name)
        self.person = person
        self.day = day

    def starts_at(self):
        """Absolute minute the shift begins, counted from day ordinal zero."""
        return self.day.toordinal() * MINUTES_PER_DAY + self.window.start

    def ends_at(self):
        return self.starts_at() + self.window.duration

    def duration(self):
        return self.window.duration

    def overlaps(self, other):
        return self.starts_at() < other.ends_at() and other.starts_at() < self.ends_at()

    def __repr__(self):
        return "Assignment(%r, %s, %r)" % (self.person, self.day, self.name)


def parse_line(line):
    """Read '2024-03-04 | ana | night' into an Assignment."""
    parts = [part.strip() for part in line.split("|")]
    if len(parts) != FIELD_COUNT:
        raise RotaError("expected %d fields: %r" % (FIELD_COUNT, line))
    day_text, person, shift = parts
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise RotaError("bad date: %r" % (day_text,))
    if not person:
        raise RotaError("missing person: %r" % (line,))
    try:
        return Assignment(person, day, shift)
    except UnknownShift as problem:
        raise RotaError(str(problem))


def load(lines):
    """Parse every line that is not blank or a comment."""
    parsed = []
    for line in lines:
        text = line.strip()
        if text and not text.startswith("#"):
            parsed.append(parse_line(text))
    return parsed


def by_person(assignments):
    """[(person, [assignments in start order]), ...] ordered by name."""
    grouped = {}
    for item in assignments:
        grouped.setdefault(item.person, []).append(item)
    return [
        (name, sorted(grouped[name], key=lambda item: item.starts_at()))
        for name in sorted(grouped)
    ]


def clashes(assignments):
    """Pairs of assignments that put one person in two places at once."""
    found = []
    for _, shifts in by_person(assignments):
        for index, first in enumerate(shifts):
            for second in shifts[index + 1:]:
                if first.overlaps(second):
                    found.append((first, second))
    return found
