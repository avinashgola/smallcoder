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
