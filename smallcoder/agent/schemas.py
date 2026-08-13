"""Structured action schemas and strict parsing of model output.

The model must reply with a single JSON object describing one action. We never
parse conversational prose heuristically: the reply is extracted as JSON,
validated with Pydantic, and per-tool arguments are validated against typed
models. Any failure raises :class:`ActionParseError` with a message that is
fed back to the model on the single reformat retry.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

ActionType = Literal["read_file", "search_code", "edit_file", "run_command", "finish"]


class AgentAction(BaseModel):
    """One structured decision from the model."""

    thought_summary: str = ""
    action_type: ActionType
    arguments: dict = Field(default_factory=dict)
    expected_result: str | None = None


class ReadFileArgs(BaseModel):
    path: str
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)


class SearchCodeArgs(BaseModel):
    query: str = Field(min_length=1)
    path: str | None = None


class EditFileArgs(BaseModel):
    path: str
    old_text: str
    new_text: str


class RunCommandArgs(BaseModel):
    command: str = Field(min_length=1)


class FinishArgs(BaseModel):
    summary: str = ""


ARG_MODELS: dict[str, type[BaseModel]] = {
    "read_file": ReadFileArgs,
    "search_code": SearchCodeArgs,
    "edit_file": EditFileArgs,
    "run_command": RunCommandArgs,
    "finish": FinishArgs,
}


class ActionParseError(Exception):
    """Raised when model output cannot be turned into a valid AgentAction."""


def extract_json_object(text: str) -> str:
    """Extract the first balanced top-level JSON object from raw model text.

    Tolerates markdown code fences and surrounding prose, since even in JSON
    mode some models wrap their answer.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    start = stripped.find("{")
    if start == -1:
        raise ActionParseError("No JSON object found in the reply.")
    depth = 0
    in_string = False
    escaped = False
    for i, ch in enumerate(stripped[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : i + 1]
    raise ActionParseError("JSON object is not closed (unbalanced braces).")


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def parse_action(text: str) -> tuple[AgentAction, BaseModel]:
    """Parse raw model text into a validated (action, typed_arguments) pair."""
    raw = extract_json_object(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ActionParseError(f"Invalid JSON: {exc.msg} at position {exc.pos}.") from exc
    if not isinstance(data, dict):
        raise ActionParseError("Reply must be a JSON object, not a list or scalar.")

    try:
        action = AgentAction.model_validate(data)
    except ValidationError as exc:
        raise ActionParseError(f"Invalid action: {_format_validation_error(exc)}") from exc

    arg_model = ARG_MODELS[action.action_type]
    try:
        typed_args = arg_model.model_validate(action.arguments)
    except ValidationError as exc:
        raise ActionParseError(
            f"Invalid arguments for {action.action_type}: {_format_validation_error(exc)}"
        ) from exc
    return action, typed_args


def action_json_schema() -> dict:
    """JSON schema used for Ollama schema-constrained output (OLLAMA_FORMAT=schema)."""
    return {
        "type": "object",
        "properties": {
            "thought_summary": {"type": "string"},
            "action_type": {
                "type": "string",
                "enum": ["read_file", "search_code", "edit_file", "run_command", "finish"],
            },
            "arguments": {"type": "object"},
            "expected_result": {"type": ["string", "null"]},
        },
        "required": ["action_type", "arguments"],
    }
