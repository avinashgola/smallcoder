import pytest

from stencil import TemplateSyntaxError, UndefinedVariable, render
from stencil.errors import UnknownFilter
from stencil.filters.numbers import comma, percent, plural, round_to
from stencil.filters.text import title, truncate
from stencil.lexer import TEXT, VAR, tokenize
from stencil.renderer import stringify


def test_tokenize_splits_text_and_placeholders():
    tokens = tokenize("Hi {{ name }}!")
    assert [token.kind for token in tokens] == [TEXT, VAR, TEXT]
    assert [token.value for token in tokens] == ["Hi ", "name", "!"]


def test_plain_substitution():
    assert render("Hello {{ name }}!", {"name": "Ada"}) == "Hello Ada!"


def test_dotted_lookup():
    assert render("{{ user.name }}", {"user": {"name": "Ada"}}) == "Ada"


def test_filters_chain_left_to_right():
    assert render("{{ name|trim|upper }}", {"name": "  ada "}) == "ADA"


def test_quoted_literal_needs_no_context():
    assert render("{{ 'raw'|upper }}") == "RAW"


def test_if_else():
    template = "{% if flag %}yes{% else %}no{% endif %}"
    assert render(template, {"flag": True}) == "yes"
    assert render(template, {"flag": []}) == "no"


def test_for_loop():
    template = "{% for item in items %}[{{ item }}]{% endfor %}"
    assert render(template, {"items": ["a", "b"]}) == "[a][b]"


def test_loop_variable_does_not_escape_the_block():
    template = "{% for x in xs %}{{ x }}{% endfor %}-{{ x }}"
    assert render(template, {"xs": [1, 2], "x": "outer"}) == "12-outer"


def test_nested_blocks():
    template = "{% for n in ns %}{% if n %}{{ n }}{% endif %}{% endfor %}"
    assert render(template, {"ns": [0, 1, 2]}) == "12"


def test_stringify():
    assert stringify(None) == ""
    assert stringify(True) == "true"
    assert stringify(False) == "false"
    assert stringify(3.0) == "3"
    assert stringify(3.5) == "3.5"


def test_missing_variable_is_reported():
    with pytest.raises(UndefinedVariable):
        render("{{ missing }}", {"name": "Ada"})


def test_unclosed_placeholder_is_reported():
    with pytest.raises(TemplateSyntaxError):
        render("{{ name")


def test_unknown_tag_is_reported():
    with pytest.raises(TemplateSyntaxError):
        render("{% while x %}{% endwhile %}")


def test_unknown_filter_is_reported():
    with pytest.raises(UnknownFilter):
        render("{{ name|shout }}", {"name": "Ada"})


def test_text_filters():
    assert title("the lord of the rings") == "The Lord of the Rings"
    assert truncate("abcdefghij", 8) == "abcde..."
    assert truncate("short", 8) == "short"


def test_number_filters():
    assert comma(1234567) == "1,234,567"
    assert comma(-1234) == "-1,234"
    assert comma(42) == "42"
    assert percent(0.256) == "26%"
    assert round_to(3.14159) == 3.14
    assert plural(1) == "" and plural(2) == "s"
