"""Loop detection over agent action fingerprints (Milestone 2A).

Small models loop: they retry an identical failing command, re-apply an edit
that already landed, or cycle between a handful of actions without changing
the repository. Every fingerprint combines the action type, normalized
arguments, affected files, the working-tree diff hash *after* the action, and
a signature of the result — so an action only counts as "the same" when it
also left the repository in the same state and produced the same outcome.

The detector only ever *reports*; the runtime decides how to intervene and
never declares success because of a detection.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Fingerprint:
    action_type: str
    args_key: str
    files_key: str
    diff_hash: str
    result_signature: str


@dataclass(frozen=True)
class LoopDetection:
    kind: str  # "exact_repetition" | "no_progress_cycle"
    count: int
    detail: str


def _normalize_value(value: object) -> object:
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def normalize_arguments(arguments: dict) -> str:
    """Canonical, whitespace-insensitive representation of tool arguments."""
    return json.dumps(
        {k: _normalize_value(v) for k, v in sorted(arguments.items())},
        sort_keys=True,
        default=str,
    )


def diff_state_hash(diff_text: str) -> str:
    """Stable short hash of the working-tree diff (repository progress marker)."""
    return hashlib.sha1(diff_text.encode("utf-8", errors="replace")).hexdigest()[:12]


@dataclass
class LoopDetector:
    """Detects exact repetition and no-progress cycles over observed actions."""

    repeat_threshold: int = 3
    no_progress_window: int = 6
    _history: list[Fingerprint] = field(default_factory=list)
    _counts: Counter = field(default_factory=Counter)

    def observe(
        self,
        action_type: str,
        arguments: dict,
        files_touched: list[str],
        diff_hash: str,
        result_signature: str,
    ) -> LoopDetection | None:
        """Record one executed action; return a detection if a loop is evident."""
        fingerprint = Fingerprint(
            action_type=action_type,
            args_key=normalize_arguments(arguments),
            files_key=",".join(sorted(files_touched)),
            diff_hash=diff_hash,
            result_signature=" ".join(result_signature.split())[:120],
        )
        self._history.append(fingerprint)
        self._counts[fingerprint] += 1

        count = self._counts[fingerprint]
        if count >= self.repeat_threshold:
            return LoopDetection(
                kind="exact_repetition",
                count=count,
                detail=(
                    f"'{action_type}' was executed {count} times with identical arguments, "
                    "an identical result, and no change to the repository"
                ),
            )

        window = self._history[-self.no_progress_window :]
        if len(window) == self.no_progress_window:
            same_repo_state = len({fp.diff_hash for fp in window}) == 1
            distinct = len(set(window))
            if same_repo_state and distinct <= self.no_progress_window // 2:
                return LoopDetection(
                    kind="no_progress_cycle",
                    count=distinct,
                    detail=(
                        f"the last {self.no_progress_window} actions cycled between only "
                        f"{distinct} distinct patterns without changing the repository"
                    ),
                )
        return None

    def reset(self) -> None:
        """Forget history after an intervention so it does not instantly retrigger."""
        self._history.clear()
        self._counts.clear()
