"""Copying record values on the way in and out of the cabinet."""


def copy_value(value):
    """Copy the containers a record can hold, share everything else."""
    if isinstance(value, dict):
        return {key: copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_value(item) for item in value]
    return value


def copy_record(record):
    """A detached copy of a whole record."""
    return {name: copy_value(value) for name, value in record.items()}


def same_record(left, right):
    """Whether two records hold the same values."""
    return copy_record(left) == copy_record(right)


def only_fields(record, names):
    """The named fields of ``record``, skipping any it does not hold."""
    return {name: copy_value(record[name]) for name in names if name in record}
