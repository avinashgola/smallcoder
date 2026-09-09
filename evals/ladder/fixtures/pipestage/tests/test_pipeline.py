from common.records import to_dicts
from pipeline.build import build_pipeline

PLAN = {
    "name": "orders",
    "stages": [
        {"type": "require", "name": "have-fields", "fields": ["region", "amount"]},
        {"type": "map", "name": "normalize-region", "field": "region",
         "using": "lower"},
        {"type": "filter", "name": "positive-amount", "field": "amount", "op": "gt",
         "value": 0},
        {"type": "group_sum", "name": "by-region", "group_by": "region",
         "value_field": "amount", "into": "total"},
        {"type": "collect", "name": "output", "into": "report_rows"},
    ],
}

ROWS = [
    {"region": "North", "amount": "120.50"},
    {"region": "north", "amount": "80"},
    {"region": "South", "amount": "-5"},
    {"amount": "12"},
    {"region": "East", "amount": "40"},
]


def make_pipeline():
    return build_pipeline(PLAN)


def test_records_come_out_grouped():
    report = make_pipeline().run(ROWS)
    assert to_dicts(report.records) == [
        {"region": "north", "total": 200.5},
        {"region": "east", "total": 40.0},
    ]


def test_report_counts_the_pass():
    report = make_pipeline().run(ROWS)
    assert report.count_in == 5
    assert report.count_out == 2
    assert report.result_for("positive-amount").dropped == 1
    assert report.result_for("have-fields").dropped == 1


def test_rejected_rows_are_reported():
    report = make_pipeline().run(ROWS)
    assert len(report.rejected()) == 2
    assert report.reject_reasons() == [
        "have-fields: missing region",
        "positive-amount: amount gt 0",
    ]


def test_artifacts_are_published():
    report = make_pipeline().run(ROWS)
    assert report.artifact("report_rows") == to_dicts(report.records)
    assert report.artifact("by-region_groups") == 2
    assert report.notes == ["output collected 2 record(s)"]


def test_run_ids_increment():
    pipeline = make_pipeline()
    assert pipeline.run(ROWS).run_id == "orders-001"
    assert pipeline.run(ROWS).run_id == "orders-002"
    assert pipeline.run(ROWS, run_id="manual").run_id == "manual"


def test_running_the_same_pipeline_twice_gives_the_same_answer():
    pipeline = make_pipeline()
    first = pipeline.run(ROWS)
    second = pipeline.run(ROWS)
    assert to_dicts(second.records) == to_dicts(first.records)
    assert len(second.rejected()) == len(first.rejected()) == 2
    assert second.reject_reasons() == first.reject_reasons()


def test_separate_pipelines_do_not_share_run_state():
    first = make_pipeline().run(ROWS)
    second = make_pipeline().run(ROWS[:2])
    assert len(first.rejected()) == 2
    assert second.rejected() == []
    assert second.artifact("by-region_groups") == 1


def test_batches_are_independent():
    pipeline = make_pipeline()
    reports = pipeline.run_batches([ROWS, ROWS[:2]])
    assert [len(report.rejected()) for report in reports] == [2, 0]


def test_report_table_and_summary():
    report = make_pipeline().run(ROWS)
    table = report.table()
    assert table.splitlines()[0].startswith("stage")
    assert "have-fields" in table
    assert report.summary_line() == "orders/orders-001: 5 in, 2 out, 2 rejected"
