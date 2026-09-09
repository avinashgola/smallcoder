"""Add and remove leading whitespace from blocks of lines."""

DEFAULT_PREFIX = "    "


def indent(lines, prefix=DEFAULT_PREFIX):
    """Prefix every non-blank line; blank lines are left alone."""
    return [prefix + line if line.strip() else line for line in lines]


def hanging_indent(lines, first="", rest=DEFAULT_PREFIX):
    """Indent the first line differently from the ones that follow it."""
    return [(first if index == 0 else rest) + line for index, line in enumerate(lines)]


def leading_spaces(line):
    """Number of spaces at the start of `line`."""
    return len(line) - len(line.lstrip(" "))


def common_prefix(lines):
    """The longest run of leading spaces shared by every non-blank line."""
    filled = [line for line in lines if line.strip()]
    if not filled:
        return ""
    return " " * min(leading_spaces(line) for line in filled)


def dedent(lines):
    """Remove the common leading indentation from a block of lines."""
    width = len(common_prefix(lines))
    if width == 0:
        return list(lines)
    return [line[width:] if line.strip() else line for line in lines]
