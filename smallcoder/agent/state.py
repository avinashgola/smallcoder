"""Agent run state: history, counters, and files touched."""

from __future__ import annotations

from dataclasses import dataclass, field

from smallcoder.agent.schemas import AgentAction


@dataclass
class StepRecord:
    step: int
    action: AgentAction | None  # None when structured output failed entirely
    observation: str
    ok: bool
    error_type: str | None = None

    def summary_line(self, max_chars: int = 160) -> str:
        """One-line compressed form used for older history in the prompt."""
        if self.action is None:
            if self.error_type == "LOOP_RESET":
                return f"Step {self.step}: strategy reset after a detected loop."
            return f"Step {self.step}: invalid model output (ignored)."
        args = self.action.arguments
        detail = args.get("path") or args.get("query") or args.get("command") or ""
        status = "ok" if self.ok else "FAILED"
        line = f"Step {self.step}: {self.action.action_type} {detail} -> {status}"
        if not self.ok:
            line += f" ({self.observation.splitlines()[0][:80]})"
        return line[:max_chars]


@dataclass
class AgentState:
    issue: str
    history: list[StepRecord] = field(default_factory=list)
    files_edited: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    error_signatures: list[str] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    structured_output_failures: int = 0
    consecutive_output_failures: int = 0
    finish_attempts: int = 0
    model_calls: int = 0
    loop_detections: int = 0
    loop_interventions: int = 0
    stall_checks: int = 0
    file_not_found_errors: int = 0
    path_suggestions_emitted: int = 0
    path_suggestions_followed: int = 0

    def record_step(self, record: StepRecord) -> None:
        self.history.append(record)

    def note_edit(self, paths: list[str]) -> None:
        for path in paths:
            if path not in self.files_edited:
                self.files_edited.append(path)

    def note_read(self, path: str) -> None:
        if path not in self.files_read:
            self.files_read.append(path)

    def note_error(self, signature: str, cap: int = 5) -> None:
        signature = signature.strip()[:160]
        if signature and signature not in self.error_signatures:
            self.error_signatures.append(signature)
            del self.error_signatures[cap:]
