"""Ollama chat client (works against any Ollama-compatible server)."""

from __future__ import annotations

import socket
import time

import httpcore
import httpx

# Private import: httpcore documents custom NetworkBackends but does not export
# its concrete stream wrapper. Pinned transitively via httpx; covered by tests.
from httpcore._backends.sync import SyncStream

from smallcoder.agent.schemas import action_json_schema
from smallcoder.models.base import ModelClientError, ModelResponse


class _IPv4Backend(httpcore.NetworkBackend):
    """httpcore network backend that resolves and connects strictly over IPv4.

    Binding a local IPv4 address (the common `curl -4` emulation) is not
    enough: on NAT64/DNS64 networks macOS getaddrinfo *synthesizes* IPv6
    addresses (64:ff9b::/96) even for IPv4 literals, so the candidate list can
    contain no usable IPv4 entry at all. Resolving with AF_INET at the source
    is the only reliable equivalent of `curl -4`.
    """

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        try:
            infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        except OSError as exc:
            raise httpcore.ConnectError(f"IPv4 resolution failed for {host!r}: {exc}") from exc
        if not infos:
            raise httpcore.ConnectError(f"No IPv4 address found for {host!r}")
        family, sock_type, proto, _, sockaddr = infos[0]
        sock = socket.socket(family, sock_type, proto)
        try:
            sock.settimeout(timeout)
            if local_address:
                sock.bind((local_address, 0))
            sock.connect(sockaddr)
            for option in socket_options or ():
                sock.setsockopt(*option)
        except OSError as exc:
            sock.close()
            raise httpcore.ConnectError(f"IPv4 connect to {host}:{port} failed: {exc}") from exc
        return SyncStream(sock)


class ForceIPv4Transport(httpx.HTTPTransport):
    """httpx transport whose connection pool uses the IPv4-only backend."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # httpx.HTTPTransport offers no public hook for a custom network
        # backend, so swap it on the underlying httpcore pool.
        self._pool._network_backend = _IPv4Backend()


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
        force_ipv4: bool = False,
    ) -> None:
        if not model:
            raise ModelClientError(
                "No model configured. Set OLLAMA_MODEL (see .env.example) or pass --model."
            )
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.structured_format = structured_format
        self.num_ctx = num_ctx
        # `curl -4` equivalent, enabled via OLLAMA_FORCE_IPV4=1. Resolution is
        # forced to AF_INET (see _IPv4Backend for why binding is insufficient).
        transport = ForceIPv4Transport() if force_ipv4 else None
        self._client = httpx.Client(timeout=request_timeout, transport=transport)

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
