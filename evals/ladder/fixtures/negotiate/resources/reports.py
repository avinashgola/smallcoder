"""Sales reports, available in several representations."""

from content.types import CSV, HTML, JSON
from serve.errors import BadRequest, NotFound

from .base import Resource
from .data import QUARTERS, REGIONS, rows_for, totals


class SalesReport(Resource):
    """The whole sales table, optionally filtered with ``?region=``."""

    offers = (JSON, CSV, HTML)
    languages = ("en", "fr")

    def collect(self, request):
        region = request.arg("region")
        if region is not None and region not in REGIONS:
            raise BadRequest("unknown region %r" % (region,))
        rows = rows_for(region=region)
        return {"title": "Sales", "rows": rows, "totals": totals(rows)}


class QuarterReport(Resource):
    """One quarter of the sales table."""

    offers = (JSON, CSV, HTML)

    def collect(self, request):
        quarter = request.var("quarter", "").lower()
        if quarter not in QUARTERS:
            raise NotFound(request.path)
        rows = rows_for(quarter=quarter)
        return {"title": "Sales %s" % quarter.upper(), "rows": rows,
                "totals": totals(rows)}


class RegionIndex(Resource):
    """The list of regions, for clients building their own filters."""

    offers = (JSON,)

    def collect(self, request):
        return {"regions": list(REGIONS), "quarters": list(QUARTERS)}
