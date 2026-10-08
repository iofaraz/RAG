import asyncio
import os

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_REQUEST_TIMEOUT_SECONDS = 15


class GeminiRequestTimeout(TimeoutError):
    """Raised when Gemini does not respond within the configured deadline."""


class GeminiServiceError(RuntimeError):
    """Raised when Gemini cannot provide a response for an application request."""


if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=GEMINI_REQUEST_TIMEOUT_SECONDS * 1000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

interactions = client.aio.interactions
interaction_retry_config = interactions.sdk_configuration.retry_config

if interaction_retry_config is None:
    raise RuntimeError("Gemini SDK did not provide an interaction retry configuration.")

interaction_retry_config.max_retries = 0
interaction_retry_config.retry_connection_errors = False


async def generate_answer(prompt: str) -> str:
    try:
        async with asyncio.timeout(GEMINI_REQUEST_TIMEOUT_SECONDS):
            interaction = await interactions.create(
                model="gemini-3.8-flash",
                input=prompt,
                timeout=GEMINI_REQUEST_TIMEOUT_SECONDS,
            )

        return interaction.output_text

    except errors.APIError as e:
        _raise_service_error(e, e.code)

    except (httpx.TimeoutException, TimeoutError) as e:
        raise GeminiRequestTimeout(
            f"Gemini request timed out after {GEMINI_REQUEST_TIMEOUT_SECONDS} seconds."
        ) from e

    except Exception as e:
        status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
        _raise_service_error(e, status_code)


def _raise_service_error(error: Exception, status_code: int | None) -> None:
    if status_code == 429:
        raise GeminiServiceError(
            "Gemini rate limit exceeded (HTTP 429). Please retry later."
        ) from error
    if status_code == 503:
        raise GeminiServiceError(
            "Gemini service is temporarily unavailable. Please try again shortly."
        ) from error
    if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
        raise GeminiServiceError(
            "Unable to connect to Gemini. Please try again shortly."
        ) from error
    raise GeminiServiceError(
        "Gemini service is unavailable. Please try again shortly."
    ) from error
