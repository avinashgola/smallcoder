"""Configuration for the report service, assembled from three layers."""

from .settings import build_stack, origins, resolve

__all__ = ["build_stack", "origins", "resolve"]
