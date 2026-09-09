import pytest

from content.accept import parse_accept, parse_accept_language, parse_quality
from content.charset import UnsupportedCharset, canonical, encode
from content.renderers import (CsvRenderer, HtmlRenderer, JsonRenderer,
                               TextRenderer, escape, renderer_for)
from content.selection import (acceptable, choose, choose_language,
                               language_quality, quality_of)
from content.types import CSV, JSON, essence, extension_for, with_charset

ROWS = [{"sku": "A-1", "name": 'Chair, "big"'}, {"sku": "B-2", "name": "Lamp"}]


def test_media_type_helpers():
    assert essence("Text/CSV; charset=utf-8") == "text/csv"
    assert extension_for(JSON) == "json"
    assert with_charset(CSV, "utf-8") == "text/csv; charset=utf-8"


def test_parse_quality():
    assert parse_quality("0.4") == 0.4
    assert parse_quality(None) == 1.0
    assert parse_quality("nonsense") == 1.0
    assert parse_quality("-1") == 0.0


def test_parse_accept_splits_and_weights():
    rankings = parse_accept("text/csv;q=0.2, application/json, */*;q=0.1")
    assert [(rank.main, rank.sub, rank.quality) for rank in rankings] == [
        ("text", "csv", 0.2), ("application", "json", 1.0), ("*", "*", 0.1)]


def test_blank_accept_means_anything():
    rankings = parse_accept(None)
    assert len(rankings) == 1
    assert rankings[0].matches("text/html")


def test_quality_prefers_the_most_specific_range():
    rankings = parse_accept("*/*;q=1.0, text/csv;q=0.2")
    assert quality_of(CSV, rankings) == 0.2
    assert quality_of(JSON, rankings) == 1.0


def test_explicit_preference_is_honoured():
    assert choose([JSON, CSV], "text/csv") == CSV
    assert choose([JSON, CSV], "text/csv;q=0.2, application/json;q=0.9") == JSON


def test_acceptable():
    assert acceptable(CSV, "text/*") is True
    assert acceptable(CSV, "application/json") is False


def test_language_selection():
    assert language_quality("en", parse_accept_language("en-GB")) == 1.0
    assert choose_language(("en", "fr"), "fr;q=0.9, en;q=0.4") == "fr"
    assert choose_language(("en", "fr"), "de") is None
    assert choose_language(("en", "fr"), None) == "en"


def test_json_renderer():
    body = JsonRenderer().render({"b": 1, "a": 2})
    assert body == '{"a":2,"b":1}'


def test_csv_renderer_quotes_cells():
    body = CsvRenderer().render({"rows": ROWS})
    assert body.splitlines() == ["sku,name", 'A-1,"Chair, ""big"""', "B-2,Lamp"]


def test_html_renderer_escapes():
    body = HtmlRenderer().render({"title": "R&D", "rows": ROWS})
    assert "<title>R&amp;D</title>" in body
    assert "&quot;big&quot;" in body
    assert escape("<b>") == "&lt;b&gt;"


def test_text_renderer():
    assert TextRenderer().render({"a": 1, "b": 2}) == "a: 1\nb: 2\n"


def test_renderer_registry():
    assert renderer_for(CSV).media_type == CSV
    with pytest.raises(KeyError):
        renderer_for("image/png")


def test_charsets():
    assert canonical("UTF8") == "utf-8"
    assert encode("ok", "ascii") == b"ok"
    with pytest.raises(UnsupportedCharset):
        encode("ok", "ebcdic")
