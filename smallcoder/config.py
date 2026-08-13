"""Environment-driven configuration.

All knobs come from environment variables (optionally loaded from a `.env`
file by the CLI). Nothing here hard-codes a host, model, or credential.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ALLOWED_COMMANDS: tuple[str, ...] = (
    "pytest",
    "python",
    "python3",
    "npm",
    "node",
    "npx",
    "ruff",
    "mypy",
)


@dataclass(frozen=True)
class Settings:
    """Resolved runtime configuration for a SmallCoder run."""

    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = ""
    structured_format: str = "json"  # "json" | "schema" | "off"

    context_limit: int = 12000  # approximate model context window, in tokens
    max_steps: int = 30
    command_timeout: int = 120  # seconds
    request_timeout: float = 300.0  # seconds, per model HTTP request
    max_tool_output_chars: int = 4000

    runs_dir: Path = Path("results/runs")
    allowed_commands: tuple[str, ...] = field(default=DEFAULT_ALLOWED_COMMANDS)

    @property
    def prompt_char_budget(self) -> int:
        """Approximate character budget for the prompt side of the context.

        Uses the documented V1 approximation of ~4 characters per token and
        reserves ~30% of the window for the model's reply and overhead.
        """
        return int(self.context_limit * 4 * 0.7)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from exc


def load_settings(**overrides: object) -> Settings:
    """Build Settings from the environment, then apply explicit overrides.

    Overrides with value ``None`` are ignored so CLI options can pass through
    unset flags without clobbering environment configuration.
    """
    allowed_raw = os.environ.get("SMALLCODER_ALLOWED_COMMANDS", "").strip()
    allowed = (
        tuple(part.strip() for part in allowed_raw.split(",") if part.strip())
        if allowed_raw
        else DEFAULT_ALLOWED_COMMANDS
    )

    values: dict[str, object] = {
        "provider": os.environ.get("SMALLCODER_PROVIDER", "ollama").strip() or "ollama",
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
        "model": os.environ.get("OLLAMA_MODEL", "").strip(),
        "structured_format": os.environ.get("OLLAMA_FORMAT", "json").strip() or "json",
        "context_limit": _env_int("SMALLCODER_CONTEXT_LIMIT", 12000),
        "max_steps": _env_int("SMALLCODER_MAX_STEPS", 30),
        "command_timeout": _env_int("SMALLCODER_COMMAND_TIMEOUT", 120),
        "request_timeout": float(_env_int("SMALLCODER_REQUEST_TIMEOUT", 300)),
        "runs_dir": Path(os.environ.get("SMALLCODER_RUNS_DIR", "results/runs")),
        "allowed_commands": allowed,
    }
    for key, value in overrides.items():
        if value is not None:
            values[key] = value
    return Settings(**values)  # type: ignore[arg-type]
