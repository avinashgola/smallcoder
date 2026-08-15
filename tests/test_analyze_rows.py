"""Tests for evals.analyze_rows against small synthetic rows fixtures."""

import json

import pytest

from evals.analyze_rows import (
    RowsError,
    check_cell_sizes,
    dedupe,
    find_duplicates,
    fisher_exact_two_sided,
    load_rows,
    main,
    summarize,
    validate_rows,
)


def make_row(**overrides):
    row = {
        "run_id": "r-000",
        "success": False,
        "stop_reason": "max_steps",
        "steps": 30,
        "tokens_in": 1000,
        "tokens_out": 100,
        "duration_s": 10.0,
        "completion_mode": "none",
        "task": "alpha",
        "trial": 1,
        "model": "model-a",
        "config": "arm-a",
    }
    row.update(overrides)
    return row


def write_rows(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(path)


@pytest.fixture
def rows_2x2(tmp_path):
    """Two models x two configs x two tasks x two trials; arm-b solves task beta."""
    rows = []
    for model in ("model-a", "model-b"):
        for config in ("arm-a", "arm-b"):
            for task in ("alpha", "beta"):
                for trial in (1, 2):
                    solved = config == "arm-b" and task == "beta"
                    rows.append(
                        make_row(
                            run_id=f"{model}-{config}-{task}-{trial}",
                            model=model,
                            config=config,
                            task=task,
                            trial=trial,
                            success=solved,
                            stop_reason="verified_stall_rescue" if solved else "max_steps",
                            completion_mode="runtime_rescued" if solved else "none",
                            steps=5 if solved else 30,
                            tokens_in=2000 if solved else 4000,
                        )
                    )
    return write_rows(tmp_path / "rows.jsonl", rows)


def test_grouping_and_aggregation(rows_2x2):
    rows = load_rows(rows_2x2)
    validate_rows(rows)
    summary = summarize(rows)

    assert summary["rows"] == 16
    assert summary["configs"] == ["arm-a", "arm-b"]
    assert len(summary["cells"]) == 4

    cell = next(
        c for c in summary["cells"] if c["model"] == "model-a" and c["config"] == "arm-b"
    )
    assert cell["n"] == 4
    assert cell["solved"] == 2
    assert cell["solve_rate"] == 0.5
    # beta solved 2/2, alpha 0/2 in this cell
    assert cell["per_task"] == {
        "alpha": {"n": 2, "solved": 0},
        "beta": {"n": 2, "solved": 2},
    }
    # mean steps: (30 + 30 + 5 + 5) / 4
    assert cell["metrics"]["steps"] == {"mean": 17.5, "n_present": 4}
    assert cell["metrics"]["tokens_in"] == {"mean": 3000.0, "n_present": 4}
    assert cell["completion_modes"] == {"none": 2, "runtime_rescued": 2}


def test_metrics_absent_from_all_rows_are_omitted(rows_2x2):
    summary = summarize(load_rows(rows_2x2))
    for cell in summary["cells"]:
        assert "file_not_found_errors" not in cell["metrics"]
        assert "path_suggestions_emitted" not in cell["metrics"]


def test_solve_rate_comparison_with_two_configs(rows_2x2):
    summary = summarize(load_rows(rows_2x2))
    comps = summary["solve_rate_comparisons"]
    combined = next(c for c in comps if c["model"] == "combined")
    assert combined["solved_a"] == "0/8"
    assert combined["solved_b"] == "4/8"
    assert combined["fisher_two_sided_p"] == pytest.approx(0.0769, abs=1e-3)


def test_duplicate_detection_and_dedupe_policies(tmp_path):
    first = make_row(run_id="first", success=True)
    second = make_row(run_id="second", success=False)
    other = make_row(run_id="other", trial=2)
    rows = load_rows(write_rows(tmp_path / "dup.jsonl", [first, second, other]))

    dups = find_duplicates(rows)
    assert list(dups) == [("model-a", "arm-a", "alpha", 1)]
    assert dups[("model-a", "arm-a", "alpha", 1)] == [1, 2]

    with pytest.raises(RowsError, match="duplicate model/config/task/trial"):
        dedupe(rows, "error")

    kept_first = dedupe(rows, "keep-first")
    assert [r["run_id"] for r in kept_first] == ["first", "other"]
    kept_last = dedupe(rows, "keep-last")
    assert [r["run_id"] for r in kept_last] == ["second", "other"]


def test_malformed_json_line_reports_line_number(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(make_row()) + "\n" + "{not json\n")
    with pytest.raises(RowsError, match="line 2: invalid JSON"):
        load_rows(str(path))


def test_non_object_row_rejected(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("[1, 2]\n")
    with pytest.raises(RowsError, match="line 1: expected a JSON object"):
        load_rows(str(path))


def test_missing_required_field_rejected(tmp_path):
    row = make_row()
    del row["config"]
    rows = load_rows(write_rows(tmp_path / "rows.jsonl", [row]))
    with pytest.raises(RowsError, match="line 1: missing required field.*config"):
        validate_rows(rows)


def test_wrong_types_rejected(tmp_path):
    rows = load_rows(write_rows(tmp_path / "rows.jsonl", [make_row(success="yes")]))
    with pytest.raises(RowsError, match="'success' must be a boolean"):
        validate_rows(rows)

    rows = load_rows(write_rows(tmp_path / "rows2.jsonl", [make_row(steps="thirty")]))
    with pytest.raises(RowsError, match="'steps' must be numeric"):
        validate_rows(rows)


def test_empty_file_rejected(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    with pytest.raises(RowsError, match="contains no rows"):
        load_rows(str(path))


def test_expected_cell_size_validation(rows_2x2):
    rows = load_rows(rows_2x2)
    check_cell_sizes(rows, 4)  # 2 tasks x 2 trials per cell: passes
    with pytest.raises(RowsError, match="expected 5 rows per model/config cell"):
        check_cell_sizes(rows, 5)


def test_fisher_exact_known_values():
    # 0/30 vs 20/30 (M2B design-set solve rates)
    assert fisher_exact_two_sided(0, 30, 20, 10) == pytest.approx(1.43e-8, rel=0.01)
    # 13/24 vs 19/24 (M3 llama solve rates)
    assert fisher_exact_two_sided(13, 11, 19, 5) == pytest.approx(0.125, abs=0.001)
    # identical arms
    assert fisher_exact_two_sided(5, 5, 5, 5) == 1.0


def test_cli_output_is_deterministic(rows_2x2, capsys):
    assert main([rows_2x2]) == 0
    first = capsys.readouterr().out
    assert main([rows_2x2]) == 0
    second = capsys.readouterr().out
    assert first == second
    assert first.startswith("# Benchmark rows summary")

    assert main([rows_2x2, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == 16
    assert payload["duplicates_resolved"] == []


def test_cli_fails_cleanly_on_duplicates(tmp_path, capsys):
    path = write_rows(
        tmp_path / "dup.jsonl", [make_row(run_id="a"), make_row(run_id="b")]
    )
    assert main([path]) == 1
    assert "duplicate model/config/task/trial" in capsys.readouterr().err
    assert main([path, "--dedupe", "keep-last"]) == 0


def test_cli_fails_on_wrong_cell_size(rows_2x2, capsys):
    assert main([rows_2x2, "--expect-cell-size", "3"]) == 1
    assert "expected 3 rows per model/config cell" in capsys.readouterr().err
