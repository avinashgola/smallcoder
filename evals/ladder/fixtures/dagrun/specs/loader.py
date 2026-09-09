"""Turn a validated specification into jobs and a dependency graph."""

from flow.graph import DependencyGraph
from flow.jobs import Job
from specs.defaults import apply_defaults, spec_defaults
from specs.expand import expand_after
from specs.validate import validate_spec
from util.ids import normalize_id


def load_spec(spec):
    """Validate `spec` and return `(jobs, groups)`."""
    groups = validate_spec(spec)
    overrides = spec_defaults(spec)
    jobs = []
    for entry in spec["jobs"]:
        merged = apply_defaults(entry, overrides)
        jobs.append(
            Job(
                id=normalize_id(merged["id"]),
                action=merged["action"],
                params=merged["params"],
                after=expand_after(merged["after"], groups),
                tags=merged["tags"],
                critical=merged["critical"],
            )
        )
    return jobs, groups


def load_jobs(spec):
    """Just the jobs, for callers that do not care about the group table."""
    jobs, _ = load_spec(spec)
    return jobs


def graph_from_jobs(jobs):
    """Build a validated graph out of already loaded jobs."""
    graph = DependencyGraph()
    for job in jobs:
        graph.add_job(job)
    for job in jobs:
        for dep in job.after:
            graph.add_dependency(job.id, dep)
    return graph.validate()


def build_graph(spec):
    """Load a specification and return its dependency graph."""
    return graph_from_jobs(load_jobs(spec))


def spec_name(spec):
    return normalize_id(spec.get("name") or "pipeline")
