"""The run loop.

`Runner` walks a `DependencyGraph` in scheduler order, calls the registered
action for each job, and turns the outcomes into a `RunReport`. Every action
receives the values produced by the jobs it depends on, so a stage can consume
its upstream output without touching global state.
"""

from flow.engine.hooks import HookBus
from flow.engine.results import JobResult, RunReport
from flow.errors import JobFailed
from flow.jobs import Status
from flow.labels import select_ids, with_ancestors
from flow.scheduler import Scheduler
from flow.state import RunState
from util.ids import run_id as make_run_id
from util.timing import StepClock


class Registry:
    """Maps action names to callables of `(job, inputs) -> value`."""

    def __init__(self, actions=None):
        self._actions = dict(actions or {})

    def register(self, name, fn=None):
        if fn is None:

            def decorator(func):
                self._actions[name] = func
                return func

            return decorator
        self._actions[name] = fn
        return fn

    def get(self, name):
        if name not in self._actions:
            raise KeyError("no action registered for %r" % (name,))
        return self._actions[name]

    def names(self):
        return sorted(self._actions)

    def __contains__(self, name):
        return name in self._actions

    def missing_for(self, graph):
        """Action names used by the graph that nothing has registered."""
        return sorted(
            {job.action for job in graph.jobs() if job.action not in self._actions}
        )


class Runner:
    """Executes a graph. One runner may be reused for many runs."""

    def __init__(self, registry, hooks=None, clock=None, max_parallel=None):
        self.registry = registry
        self.hooks = hooks or HookBus()
        self.clock = clock or StepClock()
        self.max_parallel = max_parallel
        self._runs = 0

    def run(self, graph, selectors=(), name="run"):
        """Execute the graph (or the selected slice of it) and report."""
        missing = self.registry.missing_for(graph)
        if missing:
            raise KeyError("unregistered actions: " + ", ".join(missing))
        target = self._narrow(graph, selectors)
        self._runs += 1
        state = RunState(make_run_id(name, self._runs), self.clock).begin()
        scheduler = Scheduler(target)
        results = {}
        order = []
        self.hooks.emit("run_start", run_id=state.run_id, jobs=target.job_ids())

        halted = False
        while not scheduler.is_done() and not halted:
            batch = scheduler.take(limit=self.max_parallel)
            for job_id in batch:
                job = target.job(job_id)
                order.append(job_id)
                result = self._execute(job, target, results, state)
                results[job_id] = result
                if result.ok:
                    scheduler.mark_succeeded(job_id)
                    continue
                for skipped_id in scheduler.mark_failed(job_id):
                    results[skipped_id] = self._skip(
                        skipped_id, "upstream %s failed" % job_id, state
                    )
                if job.critical:
                    halted = True
                    break

        for job_id in list(scheduler.remaining()):
            if scheduler.status_of(job_id) in Status.TERMINAL:
                continue
            results[job_id] = self._skip(job_id, "run halted", state)
            scheduler.mark_skipped(job_id)

        elapsed = state.finish()
        report = RunReport(
            state.run_id,
            [results[job_id] for job_id in target.job_ids() if job_id in results],
            order,
            elapsed,
        )
        self.hooks.emit("run_end", run_id=state.run_id, report=report)
        return report

    # -- internals -------------------------------------------------------

    def _narrow(self, graph, selectors):
        if not selectors:
            return graph
        chosen = select_ids(graph.jobs(), selectors)
        return graph.subgraph(with_ancestors(graph, chosen))

    def _inputs_for(self, job, graph, results):
        """Values produced by the jobs this one depends on."""
        inputs = {}
        for dep in graph.dependencies_of(job.id):
            if dep in results and results[dep].ok:
                inputs[dep] = results[dep].value
        return inputs

    def _execute(self, job, graph, results, state):
        state.start_job(job.id)
        self.hooks.emit("job_start", run_id=state.run_id, job_id=job.id)
        action = self.registry.get(job.action)
        inputs = self._inputs_for(job, graph, results)
        try:
            value = action(job, inputs)
        except JobFailed as failure:
            record = state.finish_job(job.id, Status.FAILED, failure.message)
            self.hooks.emit(
                "job_failure", run_id=state.run_id, job_id=job.id, error=failure.message
            )
            return JobResult(
                job.id, Status.FAILED, None, failure.message, record.duration
            )
        except Exception as exc:  # unexpected action errors are still job failures
            detail = "%s: %s" % (type(exc).__name__, exc)
            record = state.finish_job(job.id, Status.FAILED, detail)
            self.hooks.emit(
                "job_failure", run_id=state.run_id, job_id=job.id, error=detail
            )
            return JobResult(job.id, Status.FAILED, None, detail, record.duration)
        record = state.finish_job(job.id, Status.SUCCEEDED)
        self.hooks.emit(
            "job_success", run_id=state.run_id, job_id=job.id, value=value
        )
        return JobResult(job.id, Status.SUCCEEDED, value, "", record.duration)

    def _skip(self, job_id, reason, state):
        state.mark(job_id, Status.SKIPPED, reason)
        self.hooks.emit(
            "job_skip", run_id=state.run_id, job_id=job_id, reason=reason
        )
        return JobResult(job_id, Status.SKIPPED, None, reason, 0.0)
