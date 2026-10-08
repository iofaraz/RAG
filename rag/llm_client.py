import asyncio
import os

import httpx
from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    RateLimitError,
)

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_REQUEST_TIMEOUT_SECONDS = 15


class LLMRequestTimeout(TimeoutError):
    """Raised when Groq does not respond within the configured deadline."""


class LLMServiceError(RuntimeError):
    """Raised when the configured LLM service cannot provide a response."""


class LLMConfigurationError(LLMServiceError):
    """Raised when required LLM configuration is missing."""


_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMConfigurationError("GROQ_API_KEY is not configured.")

    if _client is None:
        _client = AsyncGroq(
            api_key=api_key,
            timeout=GROQ_REQUEST_TIMEOUT_SECONDS,
            max_retries=0,
        )
    return _client


async def generate_answer(prompt: str) -> str:
    client = _get_client()

    try:
        async with asyncio.timeout(GROQ_REQUEST_TIMEOUT_SECONDS):
            completion = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                timeout=GROQ_REQUEST_TIMEOUT_SECONDS,
            )
    except (APITimeoutError, httpx.TimeoutException, TimeoutError) as exc:
        raise LLMRequestTimeout(
            f"LLM request timed out after {GROQ_REQUEST_TIMEOUT_SECONDS} seconds."
        ) from exc
    except RateLimitError as exc:
        raise LLMServiceError(
            "The LLM service is rate limited. Please try again later."
        ) from exc
    except APIConnectionError as exc:
        raise LLMServiceError(
            "Unable to connect to the LLM service. Please try again shortly."
        ) from exc
    except APIStatusError as exc:
        if exc.status_code == 429:
            message = "The LLM service is rate limited. Please try again later."
        elif exc.status_code == 503:
            message = "The LLM service is temporarily unavailable. Please try again shortly."
        else:
            message = "The LLM service could not complete the request. Please try again shortly."
        raise LLMServiceError(message) from exc
    except Exception as exc:
        raise LLMServiceError(
            "The LLM service is unavailable. Please try again shortly."
        ) from exc

    if not completion.choices or not completion.choices[0].message.content:
        raise LLMServiceError("The LLM service returned an empty response.")

    return completion.choices[0].message.content
