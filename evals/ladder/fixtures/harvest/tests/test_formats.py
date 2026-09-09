import json

from execution.errors import StageFailure
from execution.rows import drop_missing
from execution.session import Session
from execution.stagerun import Stage, stage
from harvester.collector import ResultCollector
from harvester.formats import render_summary, to_csv_lines, to_dict, to_json
from harvester.formats.csvout import escape, to_csv
from harvester.formats.text import render_hotspots, render_table_for
from toolkit.timing import TickClock

ROWS = [
    {"id": 1, "amount": "10"},
    {"id": 2, "amount": "5"},
    {"id": 3},
    {"id": 4, "amount": "7"},
]


@stage("load")
def load(rows):
    return list(rows)


@stage("clean")
def clean(rows):
    return drop_missing(rows, ["amount"])


@stage("export")
def export(rows):
    return list(rows)


def broken(rows):
    raise StageFailure("upstream schema changed")


def summary_for(stages):
    session = Session("demo", stages, clock=TickClock(step=0.5))
    return ResultCollector("demo", run_id="demo-001").collect(session.run(ROWS))


def clean_summary():
    return summary_for([load, clean, export])


def failed_summary():
    return summary_for([load, Stage("clean", broken), export])


def test_table_lists_every_stage_of_a_clean_run():
    table = render_table_for(clean_summary())
    lines = table.splitlines()
    assert lines[0].startswith("stage")
    assert [line.split()[0] for line in lines[2:]] == ["load", "clean", "export"]


def test_table_lists_the_stages_that_ran_after_a_failure():
    table = render_table_for(failed_summary())
    assert [line.split()[0] for line in table.splitlines()[2:]] == [
        "load",
        "clean",
        "export",
    ]


def test_report_shows_the_failure_detail():
    report = render_summary(failed_summary())
    assert "failures:" in report
    assert "clean: upstream schema changed" in report
    assert "slowest:" in report


def test_report_of_a_clean_run_has_no_failure_block():
    report = render_summary(clean_summary())
    assert "failures:" not in report
    assert "dropped: clean 1" in report


def test_hotspots_name_the_slowest_stages():
    assert render_hotspots(clean_summary(), count=1).startswith("slowest: ")


def test_csv_has_one_line_per_stage():
    lines = to_csv_lines(failed_summary())
    assert lines[0] == "stage,state,rows_in,rows_out,duration,error"
    assert len(lines) == 4
    assert lines[1].startswith("load,done,4,4,")
    assert to_csv(clean_summary()).count("\n") == 3


def test_csv_escaping():
    assert escape(None) == ""
    assert escape("plain") == "plain"
    assert escape("a,b") == '"a,b"'
    assert escape('say "hi"') == '"say ""hi"""'


def test_json_describes_the_whole_run():
    data = to_dict(failed_summary())
    assert [stage["stage"] for stage in data["stages"]] == ["load", "clean", "export"]
    assert data["failed"] == ["clean"]
    assert data["sealed"] is True
    assert data["rows_out"] == 4


def test_json_round_trips():
    payload = json.loads(to_json(clean_summary(), indent=2))
    assert payload["run_id"] == "demo-001"
    assert payload["rows_in"] == 4
    assert len(payload["stages"]) == 3
