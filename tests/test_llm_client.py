import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from groq import APIConnectionError, APIStatusError, RateLimitError
from fastapi.testclient import TestClient


def _load_llm_client(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    llm_client = importlib.import_module("rag.llm_client")
    monkeypatch.setattr(llm_client, "_client", None)
    return llm_client


def _mock_client(monkeypatch, llm_client, create):
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        ),
    )
    monkeypatch.setattr(llm_client, "_client", client)
    return client


def _completion(content="An answer"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )


def test_generate_answer_sends_prompt_to_groq_model(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    create = AsyncMock(return_value=_completion())
    _mock_client(monkeypatch, llm_client, create)

    assert asyncio.run(llm_client.generate_answer("A focused nutrition prompt")) == "An answer"
    assert create.call_args.kwargs["model"] == "openai/gpt-oss-120b"
    assert create.call_args.kwargs["messages"] == [
        {"role": "user", "content": "A focused nutrition prompt"}
    ]
    assert create.call_args.kwargs["timeout"] == 15


def test_groq_client_disables_retries(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    fake_client = Mock()
    groq_client = Mock(return_value=fake_client)
    monkeypatch.setattr(llm_client, "AsyncGroq", groq_client)

    assert llm_client._get_client() is fake_client
    assert groq_client.call_args.kwargs["api_key"] == "test-api-key"
    assert groq_client.call_args.kwargs["timeout"] == 15
    assert groq_client.call_args.kwargs["max_retries"] == 0


def test_missing_groq_api_key_is_a_safe_configuration_error(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    monkeypatch.delenv("GROQ_API_KEY")

    with pytest.raises(llm_client.LLMConfigurationError, match="not configured"):
        asyncio.run(llm_client.generate_answer("A prompt"))


def test_generate_answer_reports_timeout(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    create = AsyncMock(side_effect=httpx.ReadTimeout("private timeout detail"))
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMRequestTimeout, match="timed out after 15 seconds"):
        asyncio.run(llm_client.generate_answer("A prompt"))


def test_generate_answer_enforces_hard_deadline(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    monkeypatch.setattr(llm_client, "GROQ_REQUEST_TIMEOUT_SECONDS", 0.01)

    async def wait_for_timeout(**_kwargs):
        await asyncio.sleep(1)

    create = AsyncMock(side_effect=wait_for_timeout)
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMRequestTimeout, match="timed out after 0.01 seconds"):
        asyncio.run(llm_client.generate_answer("A prompt"))

    create.assert_awaited_once()


def test_generate_answer_handles_rate_limit_without_retries(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, request=request)
    error = RateLimitError("private quota detail", response=response, body=None)
    create = AsyncMock(side_effect=error)
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMServiceError) as raised:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "rate limited" in str(raised.value)
    assert "private quota detail" not in str(raised.value)
    create.assert_awaited_once()


def test_generate_answer_handles_connection_failure_without_details(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    error = APIConnectionError(message="private connection detail", request=request)
    create = AsyncMock(side_effect=error)
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMServiceError) as raised:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "Unable to connect" in str(raised.value)
    assert "private connection detail" not in str(raised.value)


def test_generate_answer_handles_service_unavailable_safely(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(503, request=request)
    error = APIStatusError("private service detail", response=response, body=None)
    create = AsyncMock(side_effect=error)
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMServiceError) as raised:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "temporarily unavailable" in str(raised.value)
    assert "private service detail" not in str(raised.value)


def test_generate_answer_sanitizes_other_api_errors(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(400, request=request)
    error = APIStatusError("private request detail", response=response, body=None)
    create = AsyncMock(side_effect=error)
    _mock_client(monkeypatch, llm_client, create)

    with pytest.raises(llm_client.LLMServiceError) as raised:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "could not complete" in str(raised.value)
    assert "private request detail" not in str(raised.value)


def test_query_hides_llm_service_error_details(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    from backend.app import main

    monkeypatch.setattr(
        main,
        "answer_query",
        AsyncMock(side_effect=llm_client.LLMServiceError("private API detail")),
    )

    response = TestClient(main.app).post(
        "/api/query",
        json={"query": "What foods are high in protein?"},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
    assert "private API detail" not in response.text


def test_query_maps_llm_timeout_to_gateway_timeout(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    from backend.app import main

    monkeypatch.setattr(
        main,
        "answer_query",
        AsyncMock(side_effect=llm_client.LLMRequestTimeout("private timeout detail")),
    )

    response = TestClient(main.app).post(
        "/api/query",
        json={"query": "What foods are high in protein?"},
    )

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]
    assert "private timeout detail" not in response.text
