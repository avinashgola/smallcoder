"""Mine real, recent bug fixes from real repositories into benchmark tasks.

This is the suite the project could not previously claim to have: bugs nobody
here authored, in code nobody here wrote, with fixes merged **after the study
models' training cutoffs** (2025-01-01 or later), so the patches cannot have
been memorized. The repositories themselves are old and famous — that is the
point: the model has seen the *library*, exactly as a real engineer's model has,
but it cannot have seen the *fix*.

Construction (the SWE-bench recipe, applied with this repo's validation bar):

1. Scan each cloned repository for post-cutoff, non-merge commits that touch
   at most three source files plus at least one test file, with a small diff
   and a fix-shaped message.
2. Snapshot the tree at the **parent** commit — the world just before the fix.
3. Apply only the fix commit's **test-side** changes. The suite must now FAIL,
   with zero collection errors: the new tests pin the bug.
4. Apply the **source-side** changes. The full suite must now PASS. This is
   self-enforcing against missing dependencies, flaky tests and mis-split
   diffs: any of them breaks step 4 and the candidate is dropped, never
   hand-repaired.
5. Extract every source hunk as an exact, unique anchored replacement (the
   contract every other suite meets). Candidates whose fix cannot be anchored
   are dropped.
6. Generate the issue text from the observed failures: the failing test ids and
   one assertion line, scrubbed of ground-truth module names. Commit subjects
   are recorded as provenance but never shown to the agent — they routinely
   name the module they fix.

Licences: every snapshot keeps its upstream LICENSE/NOTICE files, and the
suite-level ATTRIBUTION.md records repo, commit, date and licence for each
task. All mined repositories are MIT/BSD/Apache-2.0.

Usage:
  python -m evals.mine_realbugs --clones <dir with git clones> [--limit 30]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_FIXTURES = ROOT / "evals" / "realbugs" / "fixtures"
OUT_TASKS = ROOT / "evals" / "realbugs" / "tasks"

CUTOFF = "2025-01-01"  # both study models' training data ends before this
MAX_SOURCE_FILES = 3
MAX_INSERTIONS = 120
MAX_PER_REPO = 8
SUITE_TIMEOUT = 100  # a fixture whose suite runs longer is unusable per-step
FIX_WORDS = ("fix", "bug", "incorrect", "wrong", "regression", "error", "crash")

STRIP_DIRS = {".git", ".github", ".circleci", ".azure-pipelines", "docs", "doc",
              ".tox", "artwork", "wheelhouse"}
STRIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".whl", ".gz", ".zip",
                  ".pdf", ".woff", ".woff2"}
MAX_FILE_BYTES = 150_000  # keep the snapshot lean; LICENSE/NOTICE always kept

CONFTEST_NOTE = "# Added by the benchmark miner: put the repository root on sys.path.\n"


def git(repo: Path, *args: str, check: bool = False) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300])
    return proc.stdout


def is_test_path(path: str) -> bool:
    return path.endswith(".py") and "test" in path.lower()


def is_source_path(path: str) -> bool:
    return (path.endswith(".py") and "test" not in path.lower()
            and Path(path).name not in ("setup.py", "conftest.py", "noxfile.py"))


def find_candidates(repo: Path) -> list[dict]:
    out = git(repo, "log", f"--since={CUTOFF}", "--no-merges", "--format=%H|%cs|%s")
    candidates = []
    for line in out.splitlines():
        sha, date, subject = line.split("|", 2)
        status = git(repo, "show", "--name-status", "--format=", sha)
        files = [(part[0], part.split("\t")[-1])
                 for part in status.strip().splitlines() if "\t" in part]
        source = [f for st, f in files if is_source_path(f) and st == "M"]
        tests = [f for st, f in files if is_test_path(f)]
        if not source or not tests or len(source) > MAX_SOURCE_FILES:
            continue
        if not any(w in subject.lower() for w in FIX_WORDS):
            continue
        stat = git(repo, "show", "--shortstat", "--format=", sha)
        m = re.search(r"(\d+) insertion", stat)
        if m and int(m.group(1)) > MAX_INSERTIONS:
            continue
        candidates.append({"sha": sha, "date": date, "subject": subject,
                           "source": source, "tests": tests})
    return candidates


def extract_snapshot(repo: Path, commit: str, dest: Path) -> None:
    """The tree at ``commit``, minus junk, licences always kept."""
    data = subprocess.run(["git", "-C", str(repo), "archive", commit],
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    # Drop symlinks outright: a dangling one (e.g. docs README.rst pointing at a
    # stripped target) makes every later copytree/stat crash, and a snapshot
    # should be self-contained anyway.
    for path in dest.rglob("*"):
        if path.is_symlink():
            path.unlink()
    for path in sorted(dest.rglob("*"), reverse=True):
        rel = path.relative_to(dest)
        name = path.name
        if any(part in STRIP_DIRS for part in rel.parts):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        elif path.is_file() and name.upper().startswith(("LICENSE", "NOTICE", "COPYING")):
            continue
        elif path.is_file() and path.suffix.lower() in STRIP_SUFFIXES:
            path.unlink(missing_ok=True)
        elif (path.is_file() and path.suffix != ".py"
              and path.stat().st_size > MAX_FILE_BYTES):
            # size cap is for junk only — a 180KB source module is realism, not junk
            path.unlink(missing_ok=True)


def ensure_conftest(fixture: Path) -> None:
    """pytest must resolve the package from the snapshot, not the environment."""
    conftest = fixture / "conftest.py"
    if (fixture / "src").is_dir():
        text = (CONFTEST_NOTE.replace("root", "src/ directory")
                + "import sys\nfrom pathlib import Path\n"
                + 'sys.path.insert(0, str(Path(__file__).parent / "src"))\n')
        existing = conftest.read_text() if conftest.is_file() else ""
        if "src" not in existing:
            conftest.write_text(text + existing, encoding="utf-8")
    elif not conftest.is_file():
        conftest.write_text(CONFTEST_NOTE, encoding="utf-8")


def apply_patch(fixture: Path, patch: str) -> bool:
    if not patch.strip():
        return False
    proc = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"],
                          cwd=fixture, input=patch, capture_output=True, text=True)
    return proc.returncode == 0


def run_suite(fixture: Path) -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "--no-header"],
            cwd=fixture, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "output": ""}
    # A failing baseline for the WRONG reason (missing dependency, collection
    # error) is self-enforcing: the fixed run fails identically and the
    # candidate is dropped, so no separate error classification is needed.
    return {"ok": proc.returncode == 0, "timeout": False,
            "output": proc.stdout + proc.stderr}


def anchored_edits(fixture: Path, repo: Path, parent: str, sha: str,
                   source_files: list[str]) -> list[dict] | None:
    """Every source hunk as an exact-unique replacement, or nothing."""
    edits = []
    for rel in source_files:
        before = git(repo, "show", f"{parent}:{rel}")
        after = git(repo, "show", f"{sha}:{rel}")
        b, a = before.splitlines(keepends=True), after.splitlines(keepends=True)
        ops = [op for op in difflib.SequenceMatcher(None, b, a).get_opcodes()
               if op[0] != "equal"]
        for _, i1, i2, j1, j2 in ops:
            found = None
            for back in range(0, 8):
                start = max(0, i1 - back)
                old = "".join(b[start:i2])
                new = "".join(b[start:i1] + a[j1:j2])
                if old and old != new and before.count(old) == 1:
                    found = {"path": rel, "old": old, "new": new}
                    break
            if found is None:
                return None
            edits.append(found)
    return edits or None


def build_issue(baseline_output: str, source_files: list[str]) -> str:
    """Failing tests + one assertion line, scrubbed of ground-truth names."""
    modules = {Path(f).stem for f in source_files}
    failing = re.findall(r"^(?:FAILED|ERROR) ([^\s]+)", baseline_output, re.M)
    detail = ""
    for line in baseline_output.splitlines():
        line = line.strip()
        if line.startswith(("E ", "assert")) or " Error" in line:
            if not any(m in line for m in modules) and "/" not in line:
                detail = line.lstrip("E ").strip()[:160]
                break
    ids = ", ".join(sorted(set(failing))[:4]) or "several tests"
    issue = f"The test suite fails: {ids}."
    if detail:
        issue += f" A failing check reports: {detail}"
    return issue


def convert_one(repo: Path, repo_name: str, cand: dict) -> tuple[str, str] | None:
    sha, parent = cand["sha"], cand["sha"] + "^"
    task_id = f"{repo_name.replace('-', '')}_{sha[:7]}"
    # Build OUTSIDE any git repository. `git apply` discovers an enclosing repo
    # and silently ignores patched paths that fall outside the current
    # directory's subtree of it — inside this project's checkout that made every
    # test patch a no-op, so baselines "passed" and every candidate was
    # rejected. In a temp dir it behaves like patch -p1, which is what we want.
    workdir = Path(tempfile.mkdtemp(prefix="realbugs-build-"))
    fixture = workdir / "fx"
    fixture.mkdir(parents=True)

    try:
        extract_snapshot(repo, parent, fixture)
    except Exception as exc:  # noqa: BLE001 - any snapshot failure just drops the candidate
        shutil.rmtree(workdir, ignore_errors=True)
        return None, f"snapshot failed: {exc}"
    ensure_conftest(fixture)
    missing = [f for f in cand["source"] if not (fixture / f).is_file()]
    if missing:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, f"source file absent from snapshot: {missing[0]}"

    test_patch = git(repo, "diff", parent, sha, "--", *cand["tests"])
    if not apply_patch(fixture, test_patch):
        shutil.rmtree(workdir, ignore_errors=True)
        return None, "test patch does not apply"

    baseline = run_suite(fixture)
    if baseline["timeout"]:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, "suite exceeds the per-step budget"
    if baseline["ok"]:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, "new tests do not fail at the parent commit"

    edits = anchored_edits(fixture, repo, parent, sha, cand["source"])
    if edits is None:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, "fix is not expressible as unique anchored replacements"

    check = Path(tempfile.mkdtemp(prefix="realbugs-check-")) / "repo"
    shutil.copytree(fixture, check)
    okay = True
    for edit in edits:
        target = check / edit["path"]
        text = target.read_text(encoding="utf-8")
        if text.count(edit["old"]) != 1:
            okay = False
            break
        target.write_text(text.replace(edit["old"], edit["new"]), encoding="utf-8")
    fixed = run_suite(check) if okay else {"ok": False}
    shutil.rmtree(check.parent, ignore_errors=True)
    if not fixed["ok"]:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, "reference edits do not make the suite pass"

    licences = [p.name for p in fixture.iterdir()
                if p.is_file() and p.name.upper().startswith(("LICENSE", "NOTICE", "COPYING"))]
    py_files = [p for p in fixture.rglob("*.py") if "__pycache__" not in p.parts]
    spec = {
        "id": task_id,
        "category": f"real bug in {repo_name} (fix merged {cand['date']}, post-cutoff)",
        "fixture": f"evals/realbugs/fixtures/{task_id}",
        "issue": build_issue(baseline["output"], cand["source"]),
        "ground_truth_files": cand["source"],
        "reference_edits": edits,
        "max_steps": 30,
        "provenance": {
            "repo": repo_name,
            "fix_commit": sha,
            "fix_date": cand["date"],
            "fix_subject": cand["subject"],
            "licence_files": licences,
            "fixture_py_bytes": sum(p.stat().st_size for p in py_files),
            "fixture_py_files": len(py_files),
        },
    }
    for cache in fixture.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    final = OUT_FIXTURES / task_id
    shutil.rmtree(final, ignore_errors=True)
    shutil.move(str(fixture), str(final))
    shutil.rmtree(workdir, ignore_errors=True)
    OUT_TASKS.mkdir(parents=True, exist_ok=True)
    (OUT_TASKS / f"{task_id}.json").write_text(json.dumps(spec, indent=2) + "\n",
                                               encoding="utf-8")
    return task_id, "imported"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.mine_realbugs")
    parser.add_argument("--clones", required=True,
                        help="directory containing git clones to mine")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args(argv)

    clones = Path(args.clones)
    OUT_FIXTURES.mkdir(parents=True, exist_ok=True)
    imported, skipped = [], []
    for repo in sorted(clones.iterdir()):
        if not (repo / ".git").exists():
            continue
        taken = 0
        for cand in find_candidates(repo):
            if taken >= MAX_PER_REPO or len(imported) >= args.limit:
                break
            try:
                task_id, why = convert_one(repo, repo.name, cand)
            except Exception as exc:  # noqa: BLE001 - one bad candidate must not kill the mine
                shutil.rmtree(OUT_FIXTURES / f"{repo.name.replace('-', '')}_{cand['sha'][:7]}",
                              ignore_errors=True)
                task_id, why = None, f"converter error: {type(exc).__name__}: {exc}"
            if task_id:
                imported.append(task_id)
                taken += 1
                print(f"[ok]   {task_id}: {cand['subject'][:70]}", flush=True)
            else:
                skipped.append((repo.name, cand["sha"][:10], why))
                print(f"[skip] {repo.name}@{cand['sha'][:10]}: {why}", flush=True)
        if len(imported) >= args.limit:
            break
    print(f"\n[realbugs] imported {len(imported)}, skipped {len(skipped)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
