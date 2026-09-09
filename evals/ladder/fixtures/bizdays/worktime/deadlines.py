"""Turn service level targets into concrete due dates."""

from worktime.business import BusinessCalendar

DEFAULT_TARGETS = {"urgent": 1, "high": 2, "normal": 5, "low": 10}


class SlaPolicy(object):
    """Maps a ticket priority onto a number of business days."""

    def __init__(self, calendar=None, targets=None):
        self.calendar = calendar or BusinessCalendar()
        self.targets = dict(DEFAULT_TARGETS if targets is None else targets)

    def target_days(self, priority):
        try:
            return self.targets[priority]
        except KeyError:
            raise ValueError("unknown priority %r" % (priority,))

    def due_date(self, opened_on, priority):
        """The business day a ticket opened on *opened_on* is due."""
        return self.calendar.add_business_days(opened_on, self.target_days(priority))

    def is_overdue(self, opened_on, priority, as_of):
        return as_of > self.due_date(opened_on, priority)

    def days_remaining(self, opened_on, priority, as_of):
        """Business days left before the due date; negative once overdue."""
        due = self.due_date(opened_on, priority)
        if as_of > due:
            return -self.calendar.business_days_between(due, as_of)
        return self.calendar.business_days_between(as_of, due)

    def triage(self, tickets, as_of):
        """Split {id: (opened_on, priority)} into overdue and on-track ids."""
        overdue = []
        on_track = []
        for ticket_id in sorted(tickets):
            opened_on, priority = tickets[ticket_id]
            bucket = overdue if self.is_overdue(opened_on, priority, as_of) else on_track
            bucket.append(ticket_id)
        return overdue, on_track
