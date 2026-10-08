import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient


def _load_llm_client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    return importlib.import_module("rag.llm_client")


def test_generate_answer_uses_seconds_for_interaction_timeout(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    create = AsyncMock(return_value=SimpleNamespace(output_text="An answer"))
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    assert asyncio.run(llm_client.generate_answer("A prompt")) == "An answer"
    assert create.call_args.kwargs["timeout"] == 15
    assert llm_client.interactions.sdk_configuration.retry_config.max_retries == 0


def test_generate_answer_reports_request_timeout(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    create = AsyncMock(side_effect=httpx.ReadTimeout("read timed out"))
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    with pytest.raises(TimeoutError, match="timed out after 15 seconds"):
        asyncio.run(llm_client.generate_answer("A prompt"))


def test_generate_answer_enforces_a_hard_deadline(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    monkeypatch.setattr(llm_client, "GEMINI_REQUEST_TIMEOUT_SECONDS", 0.01)

    async def wait_for_timeout(**_kwargs):
        await asyncio.sleep(1)

    create = AsyncMock(side_effect=wait_for_timeout)
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    with pytest.raises(llm_client.GeminiRequestTimeout, match="timed out after 0.01 seconds"):
        asyncio.run(llm_client.generate_answer("A prompt"))

    create.assert_awaited_once()


def test_generate_answer_reports_rate_limit_without_retry(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)

    class RateLimitError(Exception):
        status_code = 429

    create = AsyncMock(side_effect=RateLimitError("daily quota exceeded"))
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    with pytest.raises(RuntimeError, match="rate limit exceeded \\(HTTP 429\\)"):
        asyncio.run(llm_client.generate_answer("A prompt"))
    create.assert_awaited_once()


def test_generate_answer_reports_service_unavailable_without_details(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)

    class ServiceUnavailableError(Exception):
        status_code = 503

    create = AsyncMock(side_effect=ServiceUnavailableError("private backend detail"))
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    with pytest.raises(llm_client.GeminiServiceError) as error:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "temporarily unavailable" in str(error.value)
    assert "private backend detail" not in str(error.value)
    create.assert_awaited_once()


def test_generate_answer_handles_connection_error_without_details(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    create = AsyncMock(side_effect=httpx.ConnectError("private connection detail"))
    monkeypatch.setattr(llm_client.client.aio.interactions, "create", create)

    with pytest.raises(llm_client.GeminiServiceError) as error:
        asyncio.run(llm_client.generate_answer("A prompt"))

    assert "Unable to connect to Gemini" in str(error.value)
    assert "private connection detail" not in str(error.value)
    create.assert_awaited_once()


def test_query_hides_gemini_service_error_details(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    from backend.app import main

    monkeypatch.setattr(
        main,
        "answer_query",
        AsyncMock(side_effect=llm_client.GeminiServiceError("private API detail")),
    )

    response = TestClient(main.app).post(
        "/api/query",
        json={"query": "What foods are high in protein?"},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
    assert "private API detail" not in response.text


def test_query_returns_gateway_timeout(monkeypatch):
    llm_client = _load_llm_client(monkeypatch)
    from backend.app import main

    monkeypatch.setattr(
        main,
        "answer_query",
        AsyncMock(
            side_effect=llm_client.GeminiRequestTimeout(
                "Gemini request timed out"
            )
        ),
    )

    response = TestClient(main.app).post(
        "/api/query",
        json={"query": "What foods are high in protein?"},
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "Gemini request timed out"


def test_query_cancels_rag_at_hard_deadline(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    from backend.app import main

    async def slow_answer_query(_query):
        await asyncio.sleep(1)

    monkeypatch.setattr(main, "RAG_REQUEST_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(main, "answer_query", slow_answer_query)

    response = TestClient(main.app).post(
        "/api/query",
        json={"query": "What foods are high in protein?"},
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "RAG request timed out after 0.01 seconds."
