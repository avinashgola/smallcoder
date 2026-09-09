"""The stage protocol.

A stage takes a list of records and returns a list of records. Anything that is
not a record - counters, rejected rows, collected output - goes into the run
context as an artifact.
"""

from common.errors import PipelineError, StageError
from common.strings import slugify
from common.validators import non_empty_string
from stages.result import StageResult


class Stage:
    """Base class every concrete stage derives from."""

    kind = "stage"

    def __init__(self, name):
        self.name = slugify(non_empty_string(name, "stage name"))

    # -- subclass hooks --------------------------------------------------

    def process(self, records, ctx):
        """Transform the batch. Subclasses must override this."""
        raise NotImplementedError("%s must implement process()" % type(self).__name__)

    def stats(self, records_in, records_out):
        """Extra counters for the result; subclasses may extend this."""
        return {}

    # -- driver ----------------------------------------------------------

    def run(self, records, ctx):
        """Process a batch, wrapping unexpected errors with the stage name."""
        records_in = list(records)
        try:
            produced = list(self.process(records_in, ctx))
        except PipelineError:
            raise
        except Exception as exc:
            raise StageError(self.name, "%s: %s" % (type(exc).__name__, exc))
        return StageResult(
            self.name,
            produced,
            len(records_in),
            stats=self.stats(records_in, produced),
        )

    def describe(self):
        return "%s (%s)" % (self.name, self.kind)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class RecordStage(Stage):
    """Convenience base for stages that look at one record at a time."""

    kind = "record"

    def handle(self, record, ctx):
        """Return a record to keep it, or None to drop it."""
        raise NotImplementedError

    def process(self, records, ctx):
        kept = []
        for record in records:
            produced = self.handle(record, ctx)
            if produced is not None:
                kept.append(produced)
        return kept
