"""Formatting helpers shared by the reporting jobs."""


def format_percent(fraction):
    return f"{fraction * 100:g}%"


def table_row(cells, width=10):
    return " | ".join(f"{cell:<{width}}" for cell in cells)
