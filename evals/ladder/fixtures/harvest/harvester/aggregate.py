"""Roll-ups computed over a list of stage outcomes."""

from execution.outcome import State
from toolkit.counters import Tally, sum_by
from toolkit.sorting import top_n
from toolkit.timing import rate_per_second, share, total_seconds


def totals(outcomes):
    """Row and time totals for one run."""
    outcomes = list(outcomes)
    duration = total_seconds(outcome.duration for outcome in outcomes)
    succeeded = [outcome for outcome in outcomes if outcome.ok]
    return {
        "stages": len(outcomes),
        "rows_in": outcomes[0].rows_in if outcomes else 0,
        "rows_out": succeeded[-1].rows_out if succeeded else 0,
        "dropped": sum(outcome.dropped for outcome in succeeded),
        "duration": duration,
    }


def state_tally(outcomes):
    """How many stages ended in each state, in first-seen order."""
    return Tally(outcomes, key=lambda outcome: outcome.state)


def dropped_per_stage(outcomes):
    """(stage, rows dropped) for every stage that lost rows."""
    tally = sum_by(
        (outcome for outcome in outcomes if outcome.dropped),
        key=lambda outcome: outcome.stage,
        value=lambda outcome: outcome.dropped,
    )
    return tally.items()


def slowest(outcomes, count=3):
    """The slowest stages, longest first."""
    return top_n(list(outcomes), key=lambda outcome: outcome.duration, count=count)


def time_share(outcomes):
    """Percentage of the run each stage took, in plan order."""
    outcomes = list(outcomes)
    whole = total_seconds(outcome.duration for outcome in outcomes)
    return [(outcome.stage, share(outcome.duration, whole)) for outcome in outcomes]


def throughput(outcomes):
    """Rows produced per second across the whole run."""
    numbers = totals(outcomes)
    return rate_per_second(numbers["rows_out"], numbers["duration"])


def merge(summaries):
    """Combine several run summaries into one set of headline numbers."""
    summaries = list(summaries)
    return {
        "runs": len(summaries),
        "stages": sum(summary.stage_count for summary in summaries),
        "failed_stages": sum(len(summary.failed) for summary in summaries),
        "rows_out": sum(summary.rows_out for summary in summaries),
        "duration": total_seconds(summary.duration for summary in summaries),
        "clean_runs": sum(1 for summary in summaries if summary.ok),
    }


def failure_reasons(outcomes):
    """Error text of every failed stage, keyed by stage name."""
    return {
        outcome.stage: outcome.error
        for outcome in outcomes
        if outcome.state == State.FAILED
    }
