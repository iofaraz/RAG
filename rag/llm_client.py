import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=API_KEY)


def generate_answer(prompt: str) -> str:
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
    )

    return interaction.output_text