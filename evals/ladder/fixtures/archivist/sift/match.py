"""Applying rules to a list of entries."""

from .rules import Rule


def check(rule):
    if not isinstance(rule, Rule):
        raise TypeError("expected a Rule, got %r" % (rule,))
    return rule


def select(entries, rule):
    """The entries the rule keeps, in the order they arrived."""
    check(rule)
    return [entry for entry in entries if rule.holds(entry)]


def first_match(entries, rule, default=None):
    check(rule)
    for entry in entries:
        if rule.holds(entry):
            return entry
    return default


def count_matching(entries, rule):
    return len(select(entries, rule))


def partition(entries, rule):
    """``(kept, dropped)`` - everything, split by the rule."""
    check(rule)
    kept = []
    dropped = []
    for entry in entries:
        (kept if rule.holds(entry) else dropped).append(entry)
    return kept, dropped


def ids_of(entries):
    return [entry.id for entry in entries]
