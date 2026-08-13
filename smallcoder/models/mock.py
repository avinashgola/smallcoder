"""Scripted mock model client for tests and offline development."""

from __future__ import annotations

import json

from smallcoder.models.base import ModelResponse


class MockModelClient:
    """Replays a fixed sequence of responses; records every prompt it saw."""

    def __init__(self, responses: list[str | dict]) -> None:
        self._responses = [
            r if isinstance(r, str) else json.dumps(r) for r in responses
        ]
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> ModelResponse:
        self.calls.append(messages)
        if not self._responses:
            raise AssertionError("MockModelClient ran out of scripted responses.")
        text = self._responses.pop(0)
        return ModelResponse(
            text=text,
            tokens_in=sum(len(m["content"]) for m in messages) // 4,
            tokens_out=len(text) // 4,
            latency_ms=1,
        )
