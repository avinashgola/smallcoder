"""Turning rows of values into text tables."""

from .columns import column_widths, detect_alignments, fit_widths, normalize_rows
from .markdown import divider_cell, markdown_table
from .table import render_row, render_table

__all__ = [
    "column_widths",
    "detect_alignments",
    "divider_cell",
    "fit_widths",
    "markdown_table",
    "normalize_rows",
    "render_row",
    "render_table",
]
