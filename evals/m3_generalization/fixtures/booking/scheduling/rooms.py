"""Room directory used by the booking front end."""

CAPACITY = {"small": 4, "medium": 8, "large": 16}


def rooms_for(attendees):
    """Names of rooms that can hold the given number of attendees."""
    return sorted(name for name, cap in CAPACITY.items() if cap >= attendees)
