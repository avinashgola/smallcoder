"""Job selectors.

Pipelines get big, so runs can be narrowed with simple selector strings:

    "tag:build"      every job carrying the 'build' tag
    "id:publish"     one job by id
    "not tag:slow"   everything except the slow jobs

Several selectors are combined with 'and' semantics: a job must match all of
them to be selected.
"""

from flow.errors import SpecError


def parse_selector(text):
    """Turn one selector string into a (negated, kind, value) triple."""
    if not isinstance(text, str) or not text.strip():
        raise SpecError("empty selector")
    parts = text.strip().split()
    negated = False
    if parts[0] == "not":
        negated = True
        parts = parts[1:]
    if len(parts) != 1:
        raise SpecError("malformed selector %r" % (text,))
    kind, _, value = parts[0].partition(":")
    if not value:
        kind, value = "id", kind
    if kind not in ("id", "tag", "action"):
        raise SpecError("unknown selector kind %r" % (kind,))
    return (negated, kind, value)


def matches(job, selector):
    """True when `job` satisfies one parsed selector."""
    negated, kind, value = selector
    if kind == "id":
        hit = job.id == value
    elif kind == "tag":
        hit = job.has_tag(value)
    else:
        hit = job.action == value
    return not hit if negated else hit


def select(jobs, selectors):
    """Every job matching all of `selectors`; empty selectors select all."""
    parsed = [parse_selector(text) for text in selectors]
    if not parsed:
        return list(jobs)
    return [job for job in jobs if all(matches(job, sel) for sel in parsed)]


def select_ids(jobs, selectors):
    return [job.id for job in select(jobs, selectors)]


def with_ancestors(graph, job_ids):
    """Expand a selection so that everything it depends on runs too."""
    wanted = set(job_ids)
    for job_id in list(job_ids):
        wanted.update(graph.ancestors_of(job_id))
    return [job_id for job_id in graph.job_ids() if job_id in wanted]
