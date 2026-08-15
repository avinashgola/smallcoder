"""Validate the frozen M3 generalization suite with zero model involvement.

Proves, for each of the 12 tasks: the spec is well-formed, every referenced
path exists, the reference `old` text matches exactly once, the fixture's own
test suite fails at baseline, applying only the declared reference fix makes
the full suite pass, and the committed fixture is never modified in the
process (all work happens on a temporary copy).
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals" / "m3_generalization" / "tasks"
REQUIRED_FIELDS = (
    "id",
    "category",
    "fixture",
    "issue",
    "ground_truth_files",
    "reference_fix",
    "max_steps",
)


def load_specs():
    return [json.loads(path.read_text()) for path in sorted(TASKS_DIR.glob("*.json"))]


TASK_IDS = [spec["id"] for spec in load_specs()]


def spec_for(task_id):
    return next(spec for spec in load_specs() if spec["id"] == task_id)


def run_fixture_pytest(cwd):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )


def fixture_digest(fixture_dir):
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in fixture_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    for path in files:
        digest.update(str(path.relative_to(fixture_dir)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_exactly_twelve_tasks():
    assert len(load_specs()) == 12


def test_unique_ids_and_no_collision_with_existing_suites():
    assert len(set(TASK_IDS)) == 12
    existing = {
        json.loads(path.read_text())["id"]
        for suite in (ROOT / "evals" / "tasks", ROOT / "evals" / "heldout" / "tasks")
        for path in suite.glob("*.json")
    }
    assert not set(TASK_IDS) & existing


def test_required_fields_and_referenced_paths():
    for spec in load_specs():
        for field in REQUIRED_FIELDS:
            assert field in spec, f"{spec.get('id')}: missing {field}"
        fixture = ROOT / spec["fixture"]
        assert fixture.is_dir(), f"{spec['id']}: fixture dir missing"
        assert (fixture / "conftest.py").is_file(), f"{spec['id']}: no root conftest"
        assert list((fixture / "tests").glob("test_*.py")), f"{spec['id']}: no tests"
        assert spec["ground_truth_files"], f"{spec['id']}: empty ground_truth_files"
        for rel in spec["ground_truth_files"]:
            assert (fixture / rel).is_file(), f"{spec['id']}: missing GT file {rel}"
        fix = spec["reference_fix"]
        assert (fixture / fix["path"]).is_file(), f"{spec['id']}: missing fix target"
        assert fix["old"] != fix["new"]
        assert isinstance(spec["max_steps"], int) and spec["max_steps"] > 0


def test_issue_text_describes_behavior_not_paths():
    for spec in load_specs():
        assert ".py" not in spec["issue"], f"{spec['id']}: issue names a file"
        assert "/" not in spec["issue"], f"{spec['id']}: issue contains a path"


def test_reference_old_text_matches_exactly_once():
    for spec in load_specs():
        target = ROOT / spec["fixture"] / spec["reference_fix"]["path"]
        count = target.read_text().count(spec["reference_fix"]["old"])
        assert count == 1, f"{spec['id']}: old text matched {count} times"


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_baseline_fails_and_reference_fix_passes(task_id, tmp_path):
    spec = spec_for(task_id)
    fixture = ROOT / spec["fixture"]
    digest_before = fixture_digest(fixture)

    workdir = tmp_path / "repo"
    shutil.copytree(fixture, workdir)

    baseline = run_fixture_pytest(workdir)
    assert baseline.returncode != 0, (
        f"{task_id}: fixture tests unexpectedly pass at baseline\n{baseline.stdout}"
    )

    target = workdir / spec["reference_fix"]["path"]
    text = target.read_text()
    old, new = spec["reference_fix"]["old"], spec["reference_fix"]["new"]
    assert text.count(old) == 1
    target.write_text(text.replace(old, new))

    fixed = run_fixture_pytest(workdir)
    assert fixed.returncode == 0, (
        f"{task_id}: tests still fail after the reference fix\n{fixed.stdout}\n{fixed.stderr}"
    )

    assert fixture_digest(fixture) == digest_before, (
        f"{task_id}: committed fixture was modified during validation"
    )
