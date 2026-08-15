"""Report formatting helpers for the analytics dashboards."""


def format_money(value):
    return f"${value:,.2f}"


def format_row(region, total, width=12):
    return f"{region:<{width}}{format_money(total):>10}"
