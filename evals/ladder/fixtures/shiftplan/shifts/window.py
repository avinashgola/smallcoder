"""A block of time inside a day, possibly running past midnight."""

from shifts.clock import MINUTES_PER_DAY, ClockError, format_span, format_time, parse_time


class Window(object):
    """Starts *start* minutes past midnight and runs for *duration* minutes."""

    def __init__(self, start, duration):
        if not 0 <= start < MINUTES_PER_DAY:
            raise ClockError("shift start out of range: %r" % (start,))
        if not 0 < duration <= MINUTES_PER_DAY:
            raise ClockError("shift length out of range: %r" % (duration,))
        self.start = start
        self.duration = duration

    @classmethod
    def from_text(cls, text):
        """Read '22:00-06:00' into a window."""
        first, separator, last = str(text).partition("-")
        if not separator:
            raise ClockError("cannot read shift window: %r" % (text,))
        start = parse_time(first)
        span = (parse_time(last) - start) % MINUTES_PER_DAY
        if span == 0:
            raise ClockError("shift window has no length: %r" % (text,))
        return cls(start, span)

    @property
    def end(self):
        """The minute past midnight the window finishes on."""
        return (self.start + self.duration) % MINUTES_PER_DAY

    @property
    def crosses_midnight(self):
        return self.start + self.duration > MINUTES_PER_DAY

    def text(self):
        return "%s-%s" % (format_time(self.start), format_time(self.end))

    def label(self):
        return "%s (%s)" % (self.text(), format_span(self.duration))

    def __eq__(self, other):
        if not isinstance(other, Window):
            return NotImplemented
        return (self.start, self.duration) == (other.start, other.duration)

    def __hash__(self):
        return hash((self.start, self.duration))

    def __repr__(self):
        return "Window(%s)" % self.text()
