"""The public API, itself built out of a versioned sub-application."""

from kernel.application import Application
from kernel.errors import NotFound
from routes.urls import url_for

from .data import ITEMS, item_by_sku


def build_v1(settings=None):
    """Version 1 of the API, mounted below the API application."""
    app = Application("api.v1", settings)

    def item_list(request):
        in_stock = request.arg("in_stock") == "1"
        rows = [dict(item) for item in ITEMS
                if not in_stock or item["stock"] > 0]
        return {"items": rows, "here": request.full_path,
                "self": url_for(app, "v1.items", script_name=request.script_name)}

    def item_detail(request):
        item = item_by_sku(request.var("sku", "").upper())
        if item is None:
            raise NotFound(request.full_path)
        return item

    def stock_report(request):
        return {"total": sum(item["stock"] for item in ITEMS),
                "skus": [item["sku"] for item in ITEMS]}

    app.get("/items", item_list, name="v1.items")
    app.get("/items/{sku}", item_detail, name="v1.item")
    app.get("/stock", stock_report, name="v1.stock")
    return app


def build_api(settings=None):
    """The API application, with version 1 mounted underneath it."""
    app = Application("api", settings)

    def status(request):
        return {"app": "api", "versions": ["v1"], "here": request.full_path}

    app.get("/status", status, name="api.status")
    app.mount("/v1", build_v1(settings), name="api.v1")
    return app
