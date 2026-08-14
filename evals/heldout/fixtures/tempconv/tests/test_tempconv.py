from tempconv import celsius_to_fahrenheit, describe, fahrenheit_to_celsius


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212


def test_fahrenheit_to_celsius_freezing():
    assert fahrenheit_to_celsius(32) == 0


def test_fahrenheit_to_celsius_boiling():
    assert fahrenheit_to_celsius(212) == 100


def test_fahrenheit_to_celsius_body_temp():
    assert round(fahrenheit_to_celsius(98.6), 1) == 37.0


def test_round_trip():
    for c in (-40, 0, 15, 37, 100):
        assert round(fahrenheit_to_celsius(celsius_to_fahrenheit(c)), 6) == c


def test_describe():
    assert describe(-5) == "freezing"
    assert describe(10) == "cold"
    assert describe(20) == "mild"
    assert describe(30) == "hot"
