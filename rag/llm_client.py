import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=30_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)


def generate_answer(prompt: str) -> str:
    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
            timeout=30_000,
        )

        return interaction.output_text

    except errors.APIError as e:
        if e.code == 429:
            raise RuntimeError(
                "Gemini rate limit exceeded (HTTP 429). Please retry later."
            ) from e
        if e.code == 503:
            raise RuntimeError(
                "Gemini service unavailable (HTTP 503). Please retry later."
            ) from e
        raise RuntimeError(
            f"Gemini API request failed (HTTP {e.code}): {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"Gemini is currently unavailable: {e}"
        ) from e