from confkit.merge import diff, merge, merge_all, prune


def test_scalar_override_wins():
    assert merge({"a": 1, "b": 2}, {"b": 3}) == {"a": 1, "b": 3}


def test_nested_mappings_are_merged_not_replaced():
    base = {"server": {"host": "localhost", "port": 80}}
    result = merge(base, {"server": {"port": 8080}})
    assert result == {"server": {"host": "localhost", "port": 8080}}


def test_none_override_leaves_base_value():
    assert merge({"level": "info"}, {"level": None}) == {"level": "info"}


def test_false_override_wins():
    assert merge({"debug": True}, {"debug": False}) == {"debug": False}


def test_zero_override_wins():
    assert merge({"retries": 3}, {"retries": 0}) == {"retries": 0}


def test_empty_list_override_clears_value():
    base = {"hosts": ["a", "b"]}
    assert merge(base, {"hosts": []}) == {"hosts": []}


def test_merge_does_not_mutate_its_inputs():
    base = {"server": {"port": 80}}
    override = {"server": {"port": 8080}}
    merge(base, override)
    assert base == {"server": {"port": 80}}
    assert override == {"server": {"port": 8080}}


def test_merge_all_applies_layers_in_order():
    layers = [{"n": 1}, {"n": 2, "m": 1}, {"n": 3}]
    assert merge_all(layers) == {"n": 3, "m": 1}


def test_prune_drops_unset_values_recursively():
    data = {"a": 1, "b": None, "c": {"d": None, "e": 2}}
    assert prune(data) == {"a": 1, "c": {"e": 2}}


def test_diff_reports_only_what_changed():
    base = {"server": {"host": "h", "port": 80}, "debug": True}
    other = {"server": {"host": "h", "port": 8080}, "debug": True}
    assert diff(base, other) == {"server": {"port": 8080}}
