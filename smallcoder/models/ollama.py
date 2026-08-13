"""Ollama chat client (works against any Ollama-compatible server)."""

from __future__ import annotations

import time

import httpx

from smallcoder.agent.schemas import action_json_schema
from smallcoder.models.base import ModelClientError, ModelResponse


class OllamaClient:
    """Minimal client for Ollama's /api/chat endpoint.

    `structured_format` controls output constraints:
      - "json":   Ollama JSON mode (broadly supported)
      - "schema": constrain to the AgentAction JSON schema (Ollama >= 0.5)
      - "off":    no constraint
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        request_timeout: float = 300.0,
        structured_format: str = "json",
        num_ctx: int | None = None,
    ) -> None:
        if not model:
            raise ModelClientError(
                "No model configured. Set OLLAMA_MODEL (see .env.example) or pass --model."
            )
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.structured_format = structured_format
        self.num_ctx = num_ctx
        self._client = httpx.Client(timeout=request_timeout)

    def _payload(self, messages: list[dict[str, str]]) -> dict:
        payload: dict = {"model": self.model, "messages": messages, "stream": False}
        if self.structured_format == "json":
            payload["format"] = "json"
        elif self.structured_format == "schema":
            payload["format"] = action_json_schema()
        options: dict = {"temperature": 0.2}
        if self.num_ctx:
            options["num_ctx"] = self.num_ctx
        payload["options"] = options
        return payload

    def complete(self, messages: list[dict[str, str]]) -> ModelResponse:
        url = f"{self.base_url}/api/chat"
        payload = self._payload(messages)
        started = time.monotonic()
        try:
            response = self._client.post(url, json=payload)
        except httpx.TransportError:
            # One retry for transient network hiccups against a remote server.
            time.sleep(1.0)
            try:
                response = self._client.post(url, json=payload)
            except httpx.TransportError as exc:
                raise ModelClientError(
                    f"Cannot reach Ollama at {self.base_url}: {exc}. "
                    "Check OLLAMA_BASE_URL and that the server is running."
                ) from exc
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code != 200:
            detail = response.text[:500]
            raise ModelClientError(
                f"Ollama returned HTTP {response.status_code} for model "
                f"{self.model!r}: {detail}"
            )
        try:
            data = response.json()
            text = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ModelClientError(
                f"Unexpected Ollama response shape: {response.text[:500]}"
            ) from exc

        return ModelResponse(
            text=text,
            tokens_in=int(data.get("prompt_eval_count") or 0),
            tokens_out=int(data.get("eval_count") or 0),
            latency_ms=latency_ms,
        )

    def close(self) -> None:
        self._client.close()
