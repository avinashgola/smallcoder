from __future__ import annotations

import httpx
import pytest

from smallcoder.models.base import ModelClientError
from smallcoder.models.ollama import OllamaClient


def _client_with_transport(handler) -> OllamaClient:
    client = OllamaClient(base_url="http://test:11434", model="test-model")
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def test_successful_completion():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": '{"action_type": "finish"}'},
                "prompt_eval_count": 120,
                "eval_count": 30,
            },
        )

    response = _client_with_transport(handler).complete([{"role": "user", "content": "hi"}])
    assert response.text == '{"action_type": "finish"}'
    assert response.tokens_in == 120
    assert response.tokens_out == 30


def test_json_format_requested():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "{}"}})

    _client_with_transport(handler).complete([{"role": "user", "content": "hi"}])
    assert seen["format"] == "json"
    assert seen["stream"] is False
    assert seen["model"] == "test-model"


def test_http_error_raises_model_client_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text='{"error": "model not found"}')

    with pytest.raises(ModelClientError, match="404"):
        _client_with_transport(handler).complete([{"role": "user", "content": "hi"}])


def test_malformed_response_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    with pytest.raises(ModelClientError, match="Unexpected"):
        _client_with_transport(handler).complete([{"role": "user", "content": "hi"}])


def test_connection_error_raises_clear_message():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ModelClientError, match="Cannot reach Ollama"):
        _client_with_transport(handler).complete([{"role": "user", "content": "hi"}])


def test_missing_model_is_configuration_error():
    with pytest.raises(ModelClientError, match="OLLAMA_MODEL"):
        OllamaClient(base_url="http://test:11434", model="")


# ------------------------------------------------------------- IPv4 forcing


def test_force_ipv4_installs_ipv4_backend():
    from smallcoder.models.ollama import ForceIPv4Transport, _IPv4Backend

    client = OllamaClient(base_url="http://test:11434", model="test-model", force_ipv4=True)
    transport = client._client._transport
    assert isinstance(transport, ForceIPv4Transport)
    assert isinstance(transport._pool._network_backend, _IPv4Backend)


def test_default_uses_stock_transport():
    from smallcoder.models.ollama import ForceIPv4Transport

    client = OllamaClient(base_url="http://test:11434", model="test-model")
    assert not isinstance(client._client._transport, ForceIPv4Transport)


def test_force_ipv4_resolves_af_inet_end_to_end(monkeypatch):
    """A real request through the IPv4 backend: resolution must use AF_INET."""
    import json
    import socket
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            body = json.dumps(
                {"message": {"content": "pong"}, "prompt_eval_count": 5, "eval_count": 2}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    families: list[int] = []
    real_gai = socket.getaddrinfo

    def spy(host, p, family=0, type=0, proto=0, flags=0):
        families.append(family)
        return real_gai(host, p, family, type, proto, flags)

    monkeypatch.setattr(socket, "getaddrinfo", spy)
    try:
        client = OllamaClient(
            base_url=f"http://127.0.0.1:{port}", model="test-model", force_ipv4=True
        )
        response = client.complete([{"role": "user", "content": "ping"}])
        assert response.text == "pong"
        assert response.tokens_in == 5
        assert socket.AF_INET in families  # backend resolved IPv4-only
        assert socket.AF_INET6 not in families
    finally:
        server.shutdown()
        server.server_close()


def test_ipv4_backend_connect_error_is_httpcore_error():
    import httpcore

    from smallcoder.models.ollama import _IPv4Backend

    with pytest.raises(httpcore.ConnectError):
        # RFC 5737 TEST-NET address: guaranteed unroutable, fails fast.
        _IPv4Backend().connect_tcp("192.0.2.1", 9, timeout=0.2)


def test_force_ipv4_client_still_completes(monkeypatch):
    # The forced-IPv4 client must behave identically at the request level.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "ok"}})

    client = OllamaClient(base_url="http://test:11434", model="test-model", force_ipv4=True)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.complete([{"role": "user", "content": "hi"}]).text == "ok"


def test_force_ipv4_env_parsing(monkeypatch):
    from smallcoder.config import load_settings

    assert load_settings().force_ipv4 is False
    for raw, expected in (("1", True), ("true", True), ("YES", True), ("0", False), ("off", False)):
        monkeypatch.setenv("OLLAMA_FORCE_IPV4", raw)
        assert load_settings().force_ipv4 is expected, raw
