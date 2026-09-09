"""Selecting subsets of outcomes for a narrower report."""

from execution.outcome import State
from toolkit.sorting import partition


def with_state(outcomes, state):
    if state not in State.ALL:
        raise ValueError("unknown state %r" % (state,))
    return [outcome for outcome in outcomes if outcome.state == state]


def failures(outcomes):
    return with_state(outcomes, State.FAILED)


def successes(outcomes):
    return with_state(outcomes, State.DONE)


def skipped(outcomes):
    return with_state(outcomes, State.SKIPPED)


def named(outcomes, names):
    wanted = set(names)
    return [outcome for outcome in outcomes if outcome.stage in wanted]


def slower_than(outcomes, seconds):
    return [outcome for outcome in outcomes if outcome.duration > seconds]


def dropping_at_least(outcomes, rows):
    return [outcome for outcome in outcomes if outcome.dropped >= rows]


def split_failures(outcomes):
    """(failed, everything else), both in the original order."""
    return partition(outcomes, lambda outcome: outcome.state == State.FAILED)


def after(outcomes, stage):
    """Every outcome recorded after the named stage."""
    names = [outcome.stage for outcome in outcomes]
    if stage not in names:
        raise KeyError("no stage named %r" % (stage,))
    return list(outcomes)[names.index(stage) + 1 :]
