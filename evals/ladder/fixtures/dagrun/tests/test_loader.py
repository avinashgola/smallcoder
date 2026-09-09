import pytest

from flow.errors import SpecError
from specs.expand import groups_containing, members_of, normalize_groups
from specs.loader import build_graph, load_spec

SPEC = {
    "name": "nightly",
    "groups": {"build": ["compile", "bundle"]},
    "jobs": [
        {"id": "compile", "action": "note", "tags": ["fast"]},
        {"id": "bundle", "action": "note", "after": ["compile"]},
        {"id": "test", "action": "note", "after": ["@build", "compile"]},
        {"id": "publish", "action": "note", "after": ["test"], "critical": False},
    ],
}


def test_jobs_are_loaded_with_defaults():
    jobs, groups = load_spec(SPEC)
    assert [job.id for job in jobs] == ["compile", "bundle", "test", "publish"]
    assert jobs[0].params == {}
    assert jobs[0].critical is True
    assert jobs[3].critical is False
    assert groups == {"build": ["compile", "bundle"]}


def test_spec_level_defaults_apply_to_every_job():
    spec = dict(SPEC, defaults={"action": "custom"})
    spec["jobs"] = [{"id": "solo"}]
    spec = {"name": "d", "defaults": {"action": "custom"}, "jobs": [{"id": "solo"}]}
    jobs, _ = load_spec(spec)
    assert jobs[0].action == "custom"


def test_group_reference_expands_to_its_members():
    graph = build_graph(SPEC)
    assert graph.dependencies_of("test") == ["compile", "bundle"]


def test_graph_edges_follow_the_spec():
    graph = build_graph(SPEC)
    assert graph.roots() == ["compile"]
    assert graph.leaves() == ["publish"]


def test_unknown_group_is_rejected():
    spec = {"jobs": [{"id": "a", "after": ["@missing"]}]}
    with pytest.raises(SpecError):
        load_spec(spec)


def test_unknown_dependency_is_rejected():
    spec = {"jobs": [{"id": "a", "after": ["ghost"]}]}
    with pytest.raises(SpecError):
        load_spec(spec)


def test_duplicate_job_id_is_rejected():
    spec = {"jobs": [{"id": "a"}, {"id": "a"}]}
    with pytest.raises(SpecError):
        load_spec(spec)


def test_unknown_job_key_is_rejected():
    spec = {"jobs": [{"id": "a", "colour": "blue"}]}
    with pytest.raises(SpecError):
        load_spec(spec)


def test_empty_spec_is_rejected():
    with pytest.raises(SpecError):
        load_spec({"jobs": []})


def test_group_helpers():
    groups = normalize_groups({"Build": ["Compile", "bundle"]})
    assert members_of(groups, "build") == ["compile", "bundle"]
    assert groups_containing(groups, "bundle") == ["build"]
