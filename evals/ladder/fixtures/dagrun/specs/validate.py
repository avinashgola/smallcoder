"""Structural checks run before a specification is turned into a graph."""

from flow.errors import SpecError
from specs.defaults import KNOWN_JOB_KEYS, KNOWN_SPEC_KEYS
from specs.expand import expand_after, normalize_groups
from util.ids import normalize_id


def check_shape(spec):
    """The spec must be a mapping with a list of job entries."""
    if not isinstance(spec, dict):
        raise SpecError("specification must be a mapping")
    unknown = sorted(set(spec) - KNOWN_SPEC_KEYS)
    if unknown:
        raise SpecError("unknown top level keys: " + ", ".join(unknown))
    jobs = spec.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise SpecError("specification needs a non-empty 'jobs' list")
    return jobs


def check_job_entry(entry, index):
    """One job entry must be a mapping with a usable id."""
    if not isinstance(entry, dict):
        raise SpecError("job entry must be a mapping", path=("jobs", index))
    if "id" not in entry:
        raise SpecError("job entry has no id", path=("jobs", index))
    unknown = sorted(set(entry) - KNOWN_JOB_KEYS)
    if unknown:
        raise SpecError(
            "unknown job keys: " + ", ".join(unknown), path=("jobs", index)
        )
    try:
        return normalize_id(entry["id"])
    except ValueError as exc:
        raise SpecError(str(exc), path=("jobs", index))


def check_unique_ids(ids):
    seen = set()
    for job_id in ids:
        if job_id in seen:
            raise SpecError("duplicate job id %r" % (job_id,))
        seen.add(job_id)
    return list(ids)


def check_references(spec, ids, groups):
    """Every dependency, and every group member, must name a declared job."""
    known = set(ids)
    for name, members in groups.items():
        for member in members:
            if member not in known:
                raise SpecError(
                    "group %r references unknown job %r" % (name, member),
                    path=("groups", name),
                )
    for entry in spec["jobs"]:
        job_id = normalize_id(entry["id"])
        for dep in expand_after(entry.get("after") or [], groups):
            if dep not in known:
                raise SpecError(
                    "job %r depends on unknown job %r" % (job_id, dep),
                    path=("jobs", job_id),
                )
            if dep == job_id:
                raise SpecError(
                    "job %r depends on itself" % (job_id,), path=("jobs", job_id)
                )
    return True


def validate_spec(spec):
    """Run every check; returns the normalised group table on success."""
    jobs = check_shape(spec)
    ids = check_unique_ids(
        [check_job_entry(entry, index) for index, entry in enumerate(jobs)]
    )
    groups = normalize_groups(spec.get("groups"))
    check_references(spec, ids, groups)
    return groups
