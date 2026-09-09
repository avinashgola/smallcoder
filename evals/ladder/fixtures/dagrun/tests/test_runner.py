from flow.engine.hooks import EventLog, HookBus
from flow.engine.runner import Registry, Runner
from flow.errors import JobFailed
from flow.jobs import Status
from specs.loader import build_graph

SPEC = {
    "name": "nightly",
    "groups": {"build": ["compile", "bundle"]},
    "jobs": [
        {"id": "compile", "action": "note", "tags": ["fast"]},
        {"id": "bundle", "action": "note", "after": ["compile"]},
        {"id": "test", "action": "note", "after": ["@build", "compile"]},
        {"id": "publish", "action": "note", "after": ["test"]},
    ],
}


def make_registry(calls, failing=()):
    registry = Registry()

    def note(job, inputs):
        calls.append(job.id)
        if job.id in failing:
            raise JobFailed(job.id, "action refused")
        return {"id": job.id, "upstream": sorted(inputs)}

    registry.register("note", note)
    return registry


def test_pipeline_with_a_group_dependency_runs_to_completion():
    calls = []
    runner = Runner(make_registry(calls))
    report = runner.run(build_graph(SPEC))
    assert calls == ["compile", "bundle", "test", "publish"]
    assert report.ok
    assert report.succeeded == ["compile", "bundle", "test", "publish"]


def test_downstream_job_receives_upstream_values():
    calls = []
    runner = Runner(make_registry(calls))
    report = runner.run(build_graph(SPEC))
    assert report.values()["test"]["upstream"] == ["bundle", "compile"]


def test_failure_skips_the_rest_of_the_branch():
    calls = []
    runner = Runner(make_registry(calls, failing={"bundle"}))
    report = runner.run(build_graph(SPEC))
    assert report.failed == ["bundle"]
    assert report.skipped == ["test", "publish"]
    assert not report.ok


def test_selector_narrows_the_run_but_keeps_ancestors():
    calls = []
    runner = Runner(make_registry(calls))
    runner.run(build_graph(SPEC), selectors=["id:bundle"])
    assert calls == ["compile", "bundle"]


def test_unregistered_action_is_reported_early():
    runner = Runner(Registry())
    try:
        runner.run(build_graph(SPEC))
    except KeyError as exc:
        assert "note" in str(exc)
    else:
        raise AssertionError("expected a KeyError")


def test_hooks_see_every_job():
    bus = HookBus()
    log = EventLog(bus)
    runner = Runner(make_registry([]), hooks=bus)
    runner.run(build_graph(SPEC))
    assert log.job_ids_for("job_start") == ["compile", "bundle", "test", "publish"]
    assert len(log.events_named("run_end")) == 1


def test_report_table_lists_every_job():
    runner = Runner(make_registry([]))
    report = runner.run(build_graph(SPEC), name="nightly")
    table = report.table()
    for job_id in ("compile", "bundle", "test", "publish"):
        assert job_id in table
    assert report.summary_line().startswith("run nightly")


def test_run_ids_are_sequential():
    runner = Runner(make_registry([]))
    first = runner.run(build_graph(SPEC), name="nightly")
    second = runner.run(build_graph(SPEC), name="nightly")
    assert first.run_id == "nightly-0001"
    assert second.run_id == "nightly-0002"
    assert Status.SUCCEEDED in {r.status for r in second.results}
