"""Deterministic path-resolution suggestions for failed file references (M3).

Small models frequently request the right file under an invented directory
(``src/tempconv.py`` when the file is ``tempconv.py``) and then repeat the same
failing reference. This module turns the bare "File not found" into an
actionable message listing real repository paths.

The tool never redirects the operation: the model must retry with a valid path,
so behaviour stays transparent and auditable. Matching is deterministic —
exact basename, then case-insensitive basename, disambiguated by the longest
matching path suffix. No fuzzy distance metrics, no embeddings, no LLM.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from smallcoder.tools.search_code import SKIP_DIRS

MAX_SCANNED_FILES = 10000
MAX_SUGGESTIONS = 5


def repo_files(repo_root: Path) -> list[str]:
    """Repository-relative paths of real files, excluding tooling/VCS noise.

    Only walks inside `repo_root`, so every suggestion is inside the sandbox
    by construction. `.git` is excluded via SKIP_DIRS.
    """
    files: list[str] = []
    root = repo_root.resolve()
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            try:
                files.append(str(path.relative_to(root)))
            except ValueError:  # pragma: no cover - rglob stays under root
                continue
        if len(files) >= MAX_SCANNED_FILES:
            break
    return files


def _suffix_match_length(requested_parts: Sequence[str], candidate: str) -> int:
    """Number of trailing path components shared by the request and candidate."""
    candidate_parts = Path(candidate).parts
    shared = 0
    for req, cand in zip(reversed(requested_parts), reversed(candidate_parts), strict=False):
        if req != cand:
            break
        shared += 1
    return shared


def _disambiguate(requested: str, candidates: list[str]) -> list[str]:
    """Prefer candidates sharing the longest trailing path suffix with the request."""
    if len(candidates) <= 1:
        return candidates
    requested_parts = Path(requested).parts
    scored = [(_suffix_match_length(requested_parts, c), c) for c in candidates]
    best = max(score for score, _ in scored)
    if best > 1:  # a longer-than-basename suffix uniquely identifies a subset
        narrowed = [c for score, c in scored if score == best]
        if len(narrowed) == 1:
            return narrowed
        candidates = narrowed
    return sorted(candidates)


def suggest_paths(requested_path: str, repository_files: Sequence[str]) -> list[str]:
    """Real repository paths that plausibly match `requested_path`.

    Returns [] when nothing plausible exists, so callers fall back to the
    ordinary file-not-found error. Never returns the requested path itself.
    """
    requested = requested_path.strip()
    if not requested:
        return []
    wanted = Path(requested).name
    if not wanted:
        return []

    exact = [f for f in repository_files if Path(f).name == wanted and f != requested]
    if exact:
        return _disambiguate(requested, exact)[:MAX_SUGGESTIONS]

    lowered = wanted.lower()
    insensitive = [
        f for f in repository_files if Path(f).name.lower() == lowered and f != requested
    ]
    if insensitive:
        return _disambiguate(requested, insensitive)[:MAX_SUGGESTIONS]

    return []


def not_found_message(requested_path: str, suggestions: Sequence[str]) -> str:
    """Build the file-not-found error, with suggestions when we have any."""
    base = f"File not found: {requested_path}"
    if not suggestions:
        return base
    if len(suggestions) == 1:
        return f"{base}\n\nDid you mean:\n- {suggestions[0]}\n\nRetry using that exact path."
    listed = "\n".join(f"- {s}" for s in suggestions)
    return f"{base}\n\nPossible matches:\n{listed}\n\nRetry using one of these exact paths."


def not_found_result(repo_root: Path, requested_path: str, enabled: bool) -> tuple[str, list[str]]:
    """Shared entry point for read_file/edit_file. Returns (message, suggestions)."""
    if not enabled:
        return not_found_message(requested_path, []), []
    suggestions = suggest_paths(requested_path, repo_files(repo_root))
    return not_found_message(requested_path, suggestions), suggestions
