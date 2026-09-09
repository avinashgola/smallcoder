"""The per-run context handed to every stage.

A context carries the run identifier, the parameters the run was started with,
and the artifacts stages produce along the way. Artifacts are the side channel
for anything that is not a record: rejected rows, counters, collected output.
Each run gets its own context, so what one run puts there is invisible to the
next one.
"""

from common.strings import truncate


class StageContext:
    """Scratch space shared by the stages of a single run."""

    def __init__(self, run_id, params=None, artifacts={}):
        self.run_id = run_id
        self.params = dict(params or {})
        self.artifacts = artifacts
        self.notes = []

    # -- parameters ------------------------------------------------------

    def param(self, name, default=None):
        return self.params.get(name, default)

    def require_param(self, name):
        if name not in self.params:
            raise KeyError("run parameter %r was not supplied" % (name,))
        return self.params[name]

    def with_params(self, **extra):
        """A context for a nested stage; artifacts start as a copy of ours."""
        merged = dict(self.params)
        merged.update(extra)
        return StageContext(self.run_id, params=merged, artifacts=dict(self.artifacts))

    # -- artifacts -------------------------------------------------------

    def put_artifact(self, name, value):
        """Store (or replace) a named artifact."""
        self.artifacts[name] = value
        return value

    def append_artifact(self, name, value):
        """Append to a list artifact, creating it on first use."""
        bucket = self.artifacts.setdefault(name, [])
        bucket.append(value)
        return bucket

    def artifact(self, name, default=None):
        return self.artifacts.get(name, default)

    def has_artifact(self, name):
        return name in self.artifacts

    def artifact_names(self):
        return sorted(self.artifacts)

    def counted(self, name):
        """Length of a list artifact, or zero when it was never written."""
        return len(self.artifacts.get(name, ()))

    # -- notes -----------------------------------------------------------

    def note(self, text):
        self.notes.append(str(text))
        return text

    def describe(self):
        return "run %s: %d artifact(s), %d note(s)" % (
            self.run_id,
            len(self.artifacts),
            len(self.notes),
        )

    def __repr__(self):
        return "StageContext(%s)" % truncate(self.run_id, 24)
