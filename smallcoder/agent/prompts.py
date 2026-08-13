"""Prompt construction, tuned for small (<12B) models.

Design notes:
- One short system prompt with the full action contract; no few-shot bloat.
- The per-step user message re-states the issue, repo map, compressed history,
  and the latest observation, so the model never depends on long chat history.
- Small models do better with terse, imperative instructions and a single
  output format than with flexible conversational protocols.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are SmallCoder, an autonomous software-engineering agent working inside a git repository.
Resolve the issue by reading code, making a minimal edit, and running tests.

Reply with EXACTLY ONE JSON object and nothing else. No markdown, no code fences, no prose.

Format:
{"thought_summary": "<1-2 short sentences: what you learned, what you do next>",
 "action_type": "<one of: read_file, search_code, edit_file, run_command, finish>",
 "arguments": {...},
 "expected_result": "<short phrase>"}

Arguments per action:
- read_file:   {"path": "src/file.py", "start_line": 1, "end_line": 80}  (lines optional)
- search_code: {"query": "text to find", "path": "optional/subdir"}      (literal text search)
- edit_file:   {"path": "src/file.py", "old_text": "<exact current text>",
                "new_text": "<replacement>"}
               old_text must match EXACTLY ONE place in the file, including whitespace.
               To create a new file use old_text: "".
- run_command: {"command": "pytest tests/test_x.py"}   (allowed: {allowed_commands})
- finish:      {"summary": "what you changed and why"}

Rules:
1. Read the relevant code before editing it.
2. Make the smallest change that fixes the issue. Do not refactor.
3. After editing, run the tests to confirm the fix.
4. Use finish only when the fix is applied and tests pass. Verification runs automatically.
5. All paths are relative to the repository root.
"""

REFORMAT_MESSAGE = """\
Your previous reply was not a valid action. Error: {error}
Reply again with EXACTLY ONE JSON object in the required format and nothing else.
"""


def system_prompt(allowed_commands: tuple[str, ...]) -> str:
    return SYSTEM_PROMPT.replace("{allowed_commands}", ", ".join(allowed_commands))


def build_user_message(
    issue: str,
    repo_map: str,
    history_lines: list[str],
    last_observation: str | None,
) -> str:
    parts = [f"# Issue\n{issue.strip()}", f"# Repository files\n{repo_map}"]
    if history_lines:
        parts.append("# Progress so far\n" + "\n".join(history_lines))
    if last_observation:
        parts.append(f"# Result of your last action\n{last_observation}")
    parts.append("What is your next action? Reply with one JSON action object.")
    return "\n\n".join(parts)
