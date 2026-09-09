import pytest

from flow.errors import GraphError
from flow.graph import DependencyGraph
from flow.jobs import Job


def build(edges, ids=("a", "b", "c", "d")):
    graph = DependencyGraph()
    for job_id in ids:
        graph.add_job(Job(job_id, "noop"))
    for downstream, upstream in edges:
        graph.add_dependency(downstream, upstream)
    return graph


def test_jobs_keep_declaration_order():
    graph = build([], ids=("zeta", "alpha", "mid"))
    assert graph.job_ids() == ["zeta", "alpha", "mid"]


def test_roots_and_leaves():
    graph = build([("b", "a"), ("c", "b"), ("d", "b")])
    assert graph.roots() == ["a"]
    assert graph.leaves() == ["c", "d"]


def test_dependents_are_reported_in_declaration_order():
    graph = build([("d", "a"), ("b", "a"), ("c", "a")])
    assert graph.dependents_of("a") == ["b", "c", "d"]


def test_unknown_job_is_rejected():
    graph = build([])
    with pytest.raises(GraphError):
        graph.add_dependency("a", "nope")


def test_duplicate_job_id_is_rejected():
    graph = build([])
    with pytest.raises(GraphError):
        graph.add_job(Job("a", "noop"))


def test_self_dependency_is_rejected():
    graph = build([])
    with pytest.raises(GraphError):
        graph.add_dependency("a", "a")


def test_cycle_detection():
    graph = build([("b", "a"), ("c", "b"), ("a", "c")])
    cycle = graph.detect_cycle()
    assert cycle is not None
    with pytest.raises(GraphError):
        graph.validate()


def test_acyclic_graph_validates():
    graph = build([("b", "a"), ("c", "b")])
    assert graph.validate() is graph
    assert graph.detect_cycle() is None


def test_ancestors_and_descendants():
    graph = build([("b", "a"), ("c", "b"), ("d", "a")])
    assert graph.ancestors_of("c") == ["a", "b"]
    assert graph.descendants_of("a") == ["b", "c", "d"]


def test_subgraph_keeps_internal_edges_only():
    graph = build([("b", "a"), ("c", "b"), ("d", "c")])
    small = graph.subgraph(["b", "c"])
    assert small.job_ids() == ["b", "c"]
    assert small.dependencies_of("b") == []
    assert small.dependencies_of("c") == ["b"]


def test_edges_listing():
    graph = build([("b", "a"), ("c", "a")])
    assert graph.edges() == [("a", "b"), ("a", "c")]
