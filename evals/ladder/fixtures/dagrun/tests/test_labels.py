import pytest

from flow.errors import SpecError
from flow.graph import DependencyGraph
from flow.jobs import Job
from flow.labels import parse_selector, select, select_ids, with_ancestors

JOBS = [
    Job("compile", "shell", tags=["build", "fast"]),
    Job("bundle", "shell", tags=["build"]),
    Job("test", "pytest", tags=["slow"]),
    Job("publish", "upload", tags=["release", "slow"]),
]


def test_parse_plain_id():
    assert parse_selector("compile") == (False, "id", "compile")


def test_parse_tag_and_negation():
    assert parse_selector("tag:build") == (False, "tag", "build")
    assert parse_selector("not tag:slow") == (True, "tag", "slow")


def test_parse_rejects_nonsense():
    with pytest.raises(SpecError):
        parse_selector("")
    with pytest.raises(SpecError):
        parse_selector("colour:blue")
    with pytest.raises(SpecError):
        parse_selector("tag:a tag:b")


def test_select_by_tag():
    assert select_ids(JOBS, ["tag:build"]) == ["compile", "bundle"]


def test_select_by_action():
    assert select_ids(JOBS, ["action:shell"]) == ["compile", "bundle"]


def test_selectors_combine_with_and():
    assert select_ids(JOBS, ["tag:build", "not tag:fast"]) == ["bundle"]


def test_no_selectors_selects_everything():
    assert len(select(JOBS, [])) == len(JOBS)


def test_with_ancestors_pulls_in_dependencies():
    graph = DependencyGraph()
    for job in JOBS:
        graph.add_job(job)
    graph.add_dependency("bundle", "compile")
    graph.add_dependency("test", "bundle")
    assert with_ancestors(graph, ["test"]) == ["compile", "bundle", "test"]
