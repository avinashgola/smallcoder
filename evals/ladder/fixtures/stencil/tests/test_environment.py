import pytest

from stencil import Environment, UndefinedVariable, render


def test_defaults_are_available_to_every_template():
    env = Environment({"brand": "Acme"})
    assert env.render("{{ brand }} rules") == "Acme rules"


def test_context_wins_over_a_default():
    env = Environment({"brand": "Acme"})
    assert env.render("{{ brand }}", {"brand": "Other"}) == "Other"


def test_register_adds_a_default():
    env = Environment()
    env.register("brand", "Acme")
    assert env.render("{{ brand }}") == "Acme"


def test_add_filter():
    env = Environment()
    env.add_filter("exclaim", lambda value: str(value) + "!")
    assert env.render("{{ word|exclaim }}", {"word": "hi"}) == "hi!"


def test_custom_filters_stay_on_their_environment():
    first = Environment()
    first.add_filter("exclaim", lambda value: str(value) + "!")
    assert "exclaim" not in Environment().filters


def test_compile_reuses_the_parsed_template():
    env = Environment()
    assert env.compile("{{ a }}") is env.compile("{{ a }}")


def test_registering_a_default_does_not_reach_other_environments():
    first = Environment()
    first.register("footer", "(c) 2024")
    second = Environment()
    assert "footer" not in second.defaults


def test_constructor_does_not_mutate_the_mapping_it_is_given():
    shared = {"brand": "Acme"}
    env = Environment(shared)
    env.register("footer", "(c) 2024")
    assert shared == {"brand": "Acme"}


def test_module_level_render_starts_empty():
    env = Environment()
    env.register("secret", "hidden")
    with pytest.raises(UndefinedVariable):
        render("{{ secret }}")
