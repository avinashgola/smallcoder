"""Validate the size-ladder and QuixBugs suites with zero model involvement.

Same contract the frozen M3 suite is held to, applied to the two new suites:
every spec is well-formed, every referenced path exists, the reference `old`
text matches exactly once, the fixture's own tests fail at baseline, applying
*only* the declared reference fix makes them pass, and the committed fixture is
never modified in the process.

It also enforces the property the M3 harness could not: **ids are unique across
every suite in the repository.** The ladder tasks were authored by six agents
working in parallel and the QuixBugs tasks were imported mechanically, so
collisions are a live risk rather than a theoretical one, and a duplicate id
would silently make two different tasks share a benchmark row key.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SUITES = {
    "ladder": ROOT / "evals" / "ladder" / "tasks",
    "quixbugs": ROOT / "evals" / "quixbugs" / "tasks",
    "realbugs": ROOT / "evals" / "realbugs" / "tasks",
}
ALL_TASK_DIRS = [
    ROOT / "evals" / "tasks",
    ROOT / "evals" / "heldout" / "tasks",
    ROOT / "evals" / "m3_generalization" / "tasks",
    *SUITES.values(),
]
REQUIRED_FIELDS = (
    "id", "category", "fixture", "issue", "ground_truth_files", "max_steps",
)


def edits_of(spec: dict) -> list[dict]:
    """A task declares either one reference_fix or a list of reference_edits.

    The realbugs suite mines real commits, whose fixes are often several hunks;
    each hunk is still held to the exact-unique-anchor contract, applied in
    order.
    """
    if "reference_edits" in spec:
        return spec["reference_edits"]
    return [spec["reference_fix"]]


def specs_in(task_dir: Path):
    return [json.loads(p.read_text()) for p in sorted(task_dir.glob("*.json"))]


def new_specs():
    return [(suite, spec) for suite, d in SUITES.items() for spec in specs_in(d)]


NEW_IDS = [f"{suite}/{spec['id']}" for suite, spec in new_specs()]


def spec_for(key):
    suite, task_id = key.split("/", 1)
    return next(s for s in specs_in(SUITES[suite]) if s["id"] == task_id)


def fixture_digest(fixture_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in fixture_dir.rglob("*")
                       if p.is_file() and "__pycache__" not in p.parts):
        digest.update(str(path.relative_to(fixture_dir)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_fixture_pytest(cwd: Path):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=cwd, capture_output=True, text=True, timeout=120,
    )


def test_suites_are_non_empty():
    for suite, task_dir in SUITES.items():
        assert specs_in(task_dir), f"{suite}: no tasks found"


def test_ids_are_unique_across_every_suite_in_the_repo():
    seen: dict[str, str] = {}
    collisions = []
    for task_dir in ALL_TASK_DIRS:
        for spec in specs_in(task_dir):
            if spec["id"] in seen:
                collisions.append(f"{spec['id']} in both {seen[spec['id']]} and {task_dir.name}")
            seen[spec["id"]] = str(task_dir)
    assert not collisions, "duplicate task ids: " + "; ".join(collisions)


@pytest.mark.parametrize("key", NEW_IDS)
def test_required_fields_and_referenced_paths(key):
    spec = spec_for(key)
    for field in REQUIRED_FIELDS:
        assert field in spec, f"{key}: missing {field}"
    fixture = ROOT / spec["fixture"]
    assert fixture.is_dir(), f"{key}: fixture dir missing"
    assert (fixture / "conftest.py").is_file(), f"{key}: no root conftest"
    # Real repositories name their test dir freely (tests/, test/, ...); the
    # verifier just runs pytest from the root, so require only that test files
    # exist somewhere in the snapshot.
    assert any(f.name.startswith("test_") and f.suffix == ".py"
               for f in fixture.rglob("*.py")), f"{key}: no tests"
    assert spec["ground_truth_files"], f"{key}: empty ground_truth_files"
    for rel in spec["ground_truth_files"]:
        assert (fixture / rel).is_file(), f"{key}: missing ground-truth file {rel}"
    assert ("reference_fix" in spec) != ("reference_edits" in spec), (
        f"{key}: declare exactly one of reference_fix / reference_edits")
    for fix in edits_of(spec):
        assert (fixture / fix["path"]).is_file(), f"{key}: missing fix target {fix['path']}"
        assert fix["old"] != fix["new"], f"{key}: a reference edit is a no-op"
    assert isinstance(spec["max_steps"], int) and spec["max_steps"] > 0
    assert not list(fixture.rglob("__pycache__")), f"{key}: fixture contains __pycache__"
    assert not (fixture / ".git").exists(), f"{key}: fixture contains a .git dir"


@pytest.mark.parametrize("key", NEW_IDS)
def test_reference_old_text_matches_exactly_once(key):
    """First edit per file must anchor in the committed file; later edits to the
    same file are checked at application time, since earlier edits change it."""
    spec = spec_for(key)
    checked: set[str] = set()
    for fix in edits_of(spec):
        if fix["path"] in checked:
            continue
        checked.add(fix["path"])
        count = (ROOT / spec["fixture"] / fix["path"]).read_text().count(fix["old"])
        assert count == 1, f"{key}:{fix['path']}: anchor matched {count} times, need exactly 1"


def test_realbugs_issues_do_not_name_the_ground_truth_module():
    """Failing test ids are allowed — a real engineer sees them — but the issue
    must never hand over the source module the fix belongs in."""
    for spec in specs_in(SUITES["realbugs"]):
        stems = {Path(f).stem for f in spec["ground_truth_files"]}
        for stem in stems:
            assert stem not in spec["issue"].replace("test_" + stem, ""), (
                f"{spec['id']}: issue names ground-truth module {stem!r}")


def test_realbugs_provenance_is_recorded_and_post_cutoff():
    for spec in specs_in(SUITES["realbugs"]):
        prov = spec.get("provenance") or {}
        for field in ("repo", "fix_commit", "fix_date", "fix_subject"):
            assert prov.get(field), f"{spec['id']}: missing provenance field {field}"
        assert prov["fix_date"] >= "2025-01-01", (
            f"{spec['id']}: fix predates the models' training cutoffs")
        fixture = ROOT / spec["fixture"]
        licences = [f for f in fixture.iterdir() if f.is_file()
                    and f.name.upper().startswith(("LICENSE", "NOTICE", "COPYING"))]
        assert licences, f"{spec['id']}: snapshot lost its upstream licence file"


def test_ladder_issues_do_not_give_away_the_location():
    """Localization is half of what the ladder measures, so its issues stay symptom-only.

    QuixBugs is exempt: its fixtures are single-module by construction, the
    module is named after the function, and the imported issue text names the
    routine. There is no localization to give away there.
    """
    for spec in specs_in(SUITES["ladder"]):
        issue = spec["issue"]
        assert ".py" not in issue, f"{spec['id']}: issue names a source file"
        # A blanket ban on "/" is wrong here: the routing and content-negotiation
        # tasks legitimately quote URLs ("GET /articles", "Accept: */*"). What must
        # not appear is a path to a file in the fixture.
        fixture = ROOT / spec["fixture"]
        for src in fixture.rglob("*.py"):
            rel = src.relative_to(fixture).as_posix()
            if "/" not in rel:
                continue
            assert rel not in issue, f"{spec['id']}: issue contains the path {rel}"
            assert rel[:-3] not in issue, f"{spec['id']}: issue contains the module path {rel[:-3]}"


def test_ladder_fixtures_are_actually_large():
    """The whole point of this suite is that the existing fixtures are ~1.6KB."""
    for spec in specs_in(SUITES["ladder"]):
        fixture = ROOT / spec["fixture"]
        files = [p for p in fixture.rglob("*.py") if "__pycache__" not in p.parts]
        total = sum(p.stat().st_size for p in files)
        assert total >= 8_000, f"{spec['id']}: only {total} bytes — not a size-ladder task"
        assert len(files) >= 5, f"{spec['id']}: only {len(files)} python files"


@pytest.mark.parametrize("key", NEW_IDS)
def test_baseline_fails_and_reference_fix_passes(key, tmp_path):
    spec = spec_for(key)
    fixture = ROOT / spec["fixture"]
    digest_before = fixture_digest(fixture)

    workdir = tmp_path / "repo"
    shutil.copytree(fixture, workdir)

    baseline = run_fixture_pytest(workdir)
    assert baseline.returncode != 0, (
        f"{key}: fixture tests unexpectedly PASS at baseline — the task measures nothing\n"
        f"{baseline.stdout[-1500:]}"
    )

    for fix in edits_of(spec):
        target = workdir / fix["path"]
        text = target.read_text()
        assert text.count(fix["old"]) == 1, (
            f"{key}:{fix['path']}: anchor not unique at application time")
        target.write_text(text.replace(fix["old"], fix["new"]))

    fixed = run_fixture_pytest(workdir)
    assert fixed.returncode == 0, (
        f"{key}: reference fix alone does not make the suite pass\n{fixed.stdout[-1500:]}"
    )
    assert fixture_digest(fixture) == digest_before, f"{key}: committed fixture was modified"
