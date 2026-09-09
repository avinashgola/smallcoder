"""Machine readable rendering."""

import json


def to_dict(summary):
    """A plain dictionary describing the whole run."""
    return {
        "run_id": summary.run_id,
        "plan": summary.plan,
        "sealed": summary.sealed,
        "rows_in": summary.rows_in,
        "rows_out": summary.rows_out,
        "duration": round(summary.duration, 6),
        "stages": [outcome.to_dict() for outcome in summary.recorded()],
        "failed": summary.failed_names(),
        "skipped": summary.skipped_names(),
    }


def to_json(summary, indent=None):
    return json.dumps(to_dict(summary), indent=indent, sort_keys=True)
