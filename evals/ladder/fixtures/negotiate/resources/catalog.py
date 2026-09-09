"""The product catalogue and the service status endpoint."""

from content.types import CSV, JSON, TEXT
from serve.errors import NotFound

from .base import Resource
from .data import CATALOG


class CatalogList(Resource):
    """Every product; CSV first because this is mostly pulled by scripts."""

    offers = (CSV, JSON)

    def collect(self, request):
        in_stock = request.arg("in_stock")
        rows = [dict(item) for item in CATALOG]
        if in_stock == "1":
            rows = [row for row in rows if row["stock"] > 0]
        return {"title": "Catalogue", "rows": rows}


class CatalogItem(Resource):
    """One product, looked up by its sku."""

    offers = (JSON, TEXT)

    def collect(self, request):
        sku = request.var("sku", "").upper()
        for item in CATALOG:
            if item["sku"] == sku:
                return dict(item)
        raise NotFound(request.path)


class ServiceStatus(Resource):
    """A liveness endpoint that machines and humans both poll."""

    offers = (JSON, TEXT)

    def collect(self, request):
        return {"status": "ok", "products": len(CATALOG)}
