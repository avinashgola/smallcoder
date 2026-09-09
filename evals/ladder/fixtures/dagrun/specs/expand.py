"""Group expansion.

A specification may declare named groups so that a job can wait for a whole
stage instead of listing its members:

    groups: {"build": ["compile", "bundle"]}
    jobs:   [{"id": "test", "after": ["@build"]}]

Group references are written with a leading '@' and are resolved here, before
the graph is built.
"""

from flow.errors import SpecError
from util.ids import group_name, is_group_ref, normalize_id


def normalize_groups(raw_groups):
    """Normalise the group table: names and members become clean ids."""
    groups = {}
    for name, members in (raw_groups or {}).items():
        key = normalize_id(name)
        if key in groups:
            raise SpecError("duplicate group %r" % (name,), path=("groups", name))
        if isinstance(members, str) or not hasattr(members, "__iter__"):
            raise SpecError("group %r must list its members" % (name,), path=("groups", name))
        groups[key] = [normalize_id(member) for member in members]
    return groups


def expand_entry(entry, groups):
    """Expand one 'after' entry into the job ids it refers to."""
    if is_group_ref(entry):
        name = group_name(entry)
        if name not in groups:
            raise SpecError("unknown group %r" % (name,), path=("after", entry))
        return list(groups[name])
    return [normalize_id(entry)]


def expand_after(entries, groups):
    """Expand every 'after' entry of one job, keeping declaration order."""
    resolved = []
    for entry in entries or ():
        resolved.extend(expand_entry(entry, groups))
    return resolved


def members_of(groups, name):
    """Members of a group, or an empty list when it is not declared."""
    return list(groups.get(normalize_id(name), ()))


def groups_containing(groups, job_id):
    """Names of the groups a job belongs to, sorted for stable output."""
    target = normalize_id(job_id)
    return sorted(name for name, members in groups.items() if target in members)
