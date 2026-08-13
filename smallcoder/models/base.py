"""Provider-agnostic model client interface."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class ModelResponse(BaseModel):
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0


class ModelClientError(Exception):
    """Inference backend failed (connection, HTTP error, bad payload)."""


class ModelClient(Protocol):
    """Anything that can turn chat messages into a completion."""

    def complete(self, messages: list[dict[str, str]]) -> ModelResponse: ...
