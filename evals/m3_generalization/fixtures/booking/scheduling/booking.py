"""Meeting-room booking conflict checks. Times are minutes since midnight."""


def overlaps(start_a, end_a, start_b, end_b):
    """True if the two half-open intervals [start, end) overlap."""
    return start_a <= end_b and start_b <= end_a


def can_book(existing, start, end):
    """True if [start, end) conflicts with none of the existing bookings."""
    if end <= start:
        raise ValueError("end must be after start")
    return all(not overlaps(start, end, s, e) for s, e in existing)


def free_slots(existing, day_start, day_end):
    """Return the maximal free [start, end) gaps between sorted bookings."""
    slots = []
    cursor = day_start
    for s, e in sorted(existing):
        if s > cursor:
            slots.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < day_end:
        slots.append((cursor, day_end))
    return slots
