"""Running queries over records."""

from .ordering import parse_orders, sort_records
from .paging import slice_page
from .parser import build_predicate
from .predicates import Always, Predicate


class Query:
    """A filter, an ordering and a window, applied in that order."""

    def __init__(self, predicate=None, order=(), limit=None, offset=0):
        self.predicate = predicate if predicate is not None else Always()
        self.order = list(order)
        self.limit = limit
        self.offset = offset

    @classmethod
    def from_spec(cls, spec):
        return cls(build_predicate(spec))

    def where(self, spec):
        """Narrow the query; the new condition is ANDed with the old one."""
        extra = spec if isinstance(spec, Predicate) else build_predicate(spec)
        if isinstance(self.predicate, Always):
            combined = extra
        else:
            combined = self.predicate & extra
        return Query(combined, self.order, self.limit, self.offset)

    def order_by(self, *specs):
        return Query(self.predicate, parse_orders(list(specs)), self.limit, self.offset)

    def page(self, limit=None, offset=0):
        return Query(self.predicate, self.order, limit, offset)

    def filter(self, records):
        """Everything that matches, in the order it arrived."""
        return [record for record in records if self.predicate.matches(record)]

    def run(self, records):
        """Filter, sort and window ``records``."""
        matched = self.filter(records)
        if self.order:
            matched = sort_records(matched, self.order)
        return slice_page(matched, self.limit, self.offset)

    def count(self, records):
        """How many records match, ignoring the window."""
        return len(self.filter(records))

    def first(self, records):
        found = self.run(records)
        return found[0] if found else None

    def fields(self):
        return self.predicate.fields()

    def __repr__(self):
        return "Query(%r, order=%r, limit=%r, offset=%r)" % (
            self.predicate,
            self.order,
            self.limit,
            self.offset,
        )


def run_spec(records, spec, order=None, limit=None, offset=0):
    """One-shot helper: build a query from ``spec`` and run it."""
    query = Query(build_predicate(spec), parse_orders(order), limit, offset)
    return query.run(records)
