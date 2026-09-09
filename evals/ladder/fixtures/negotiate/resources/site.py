"""Wiring for the demo server."""

from serve.application import Server

from .catalog import CatalogItem, CatalogList, ServiceStatus
from .reports import QuarterReport, RegionIndex, SalesReport


def build_server(**settings):
    """The server as the service starts it."""
    server = Server(**settings)
    server.resource("/reports/sales", SalesReport(), name="reports.sales")
    server.resource("/reports/sales/:quarter", QuarterReport(), name="reports.quarter")
    server.resource("/reports/regions", RegionIndex(), name="reports.regions")
    server.resource("/catalog", CatalogList(), name="catalog.list")
    server.resource("/catalog/:sku", CatalogItem(), name="catalog.item")
    server.resource("/status", ServiceStatus(), name="status")
    return server
