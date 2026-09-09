"""The opcode vocabulary every part of the differ shares."""

from collections import namedtuple

EQUAL = "equal"
DELETE = "delete"
INSERT = "insert"

# One line of the diff. `old` and `new` are the zero-based line numbers on
# each side, and are None when the line does not exist on that side.
Op = namedtuple("Op", "tag line old new")


def equal(line, old, new):
    """A line present, unchanged, on both sides."""
    return Op(EQUAL, line, old, new)


def delete(line, old):
    """A line that only exists in the original."""
    return Op(DELETE, line, old, None)


def insert(line, new):
    """A line that only exists in the updated version."""
    return Op(INSERT, line, None, new)


def has_changes(ops):
    """True when the two sides are not identical."""
    return any(op.tag == DELETE for op in ops)


def counts(ops):
    """How many lines were added and how many were removed."""
    added = sum(1 for op in ops if op.tag == INSERT)
    removed = sum(1 for op in ops if op.tag == DELETE)
    return added, removed


def old_side(ops):
    """Rebuild the original sequence from a list of ops."""
    return [op.line for op in ops if op.tag != INSERT]


def new_side(ops):
    """Rebuild the updated sequence from a list of ops."""
    return [op.line for op in ops if op.tag != DELETE]
