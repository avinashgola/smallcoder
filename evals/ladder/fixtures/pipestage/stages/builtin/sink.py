"""Terminal stages that publish records as artifacts."""

from common.records import to_dicts
from common.validators import non_empty_string
from stages.base import Stage


class CollectStage(Stage):
    """Store the batch as an artifact and pass it on unchanged."""

    kind = "collect"

    def __init__(self, name, into="collected", as_dicts=True):
        super().__init__(name)
        self.into = non_empty_string(into, "into", where=name)
        self.as_dicts = bool(as_dicts)

    def process(self, records, ctx):
        payload = to_dicts(records) if self.as_dicts else list(records)
        ctx.put_artifact(self.into, payload)
        ctx.note("%s collected %d record(s)" % (self.name, len(payload)))
        return list(records)

    def stats(self, records_in, records_out):
        return {"collected": len(records_in), "into": self.into}
