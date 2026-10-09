import asyncio
import logging
import re

from .retriever import retrieve_foods
from .llm_client import generate_answer
from graph.graph_retriever import retrieve_from_graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
NUMBER_PATTERN = re.compile(r"(?<!\w)\d+(?:\.\d+)?(?!\w)")
RANGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\b")
UNSUPPORTED_BASIS_PATTERN = re.compile(
    r"\b(?:typical serving|per (?:the )?(?:listed )?serving|portion shown|whole foods?)\b",
    flags=re.IGNORECASE,
)


def _has_unsupported_numbers(answer, context):
    context_normalized = context.casefold()
    if any(
        phrase.casefold() not in context_normalized
        for phrase in UNSUPPORTED_BASIS_PATTERN.findall(answer)
    ):
        return True

    if any(match.group(0).casefold() not in context_normalized for match in RANGE_PATTERN.finditer(answer)):
        return True

    context_tokens = set(re.findall(r"[a-z0-9]+", context_normalized))
    for line in answer.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("*").strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0].casefold().startswith("food ("):
            continue
        food_tokens = re.findall(r"[a-z0-9]+", cells[0].casefold())
        if food_tokens and any(token not in context_tokens for token in food_tokens):
            return True

    context_numbers = NUMBER_PATTERN.findall(context)
    context_values = [float(number) for number in context_numbers]
    exact_numbers = set(context_numbers)

    for number in NUMBER_PATTERN.findall(answer):
        if number in exact_numbers:
            continue

        precision = len(number.partition(".")[2])
        value = float(number)
        if not any(round(context_value, precision) == value for context_value in context_values):
            return True

    return False


def _retrieved_facts_summary(results, graph_result):
    facts = []
    seen = set()

    def add_fact(food, value, unit, nutrient, basis=None):
        if food is None or value is None:
            return
        key = (str(food).strip().casefold(), str(value), str(unit).casefold(), str(nutrient).casefold())
        if key in seen:
            return
        seen.add(key)
        measurement = " ".join(part for part in (str(value), unit, nutrient) if part)
        if basis:
            measurement = f"{measurement} ({basis})"
        facts.append(f"{food}: {measurement}")

    for item in graph_result.get("results", []):
        add_fact(
            item.get("food"),
            item.get("amount"),
            item.get("unit"),
            item.get("nutrient"),
            item.get("basis"),
        )

    for item in results:
        nutrient = item.get("nutrient")
        document = item.get("document", "")
        unit_match = re.search(
            rf"^\s*{re.escape(str(nutrient))}\s*:\s*[-+]?\d*\.?\d+\s*(\S+)",
            document,
            flags=re.IGNORECASE | re.MULTILINE,
        ) if nutrient else None
        add_fact(
            item.get("food"),
            item.get("value"),
            unit_match.group(1) if unit_match else None,
            nutrient,
        )

    if not facts:
        return "The retrieved records do not provide enough detail to answer this question."
    return "The retrieved records report: " + "; ".join(facts) + "."


def build_context(results):
    context = []

    for i, result in enumerate(results, start=1):
        context.append(
            f"""
            Food {i}:
            {result["document"]}
            """
        )

    return "\n".join(context)


async def answer_question(question):
    print("RAG: starting retrieval", flush=True)
    logger.info("RAG retrieval started")
    results = await asyncio.to_thread(retrieve_foods, question)

    print(f"RAG: Chroma retrieval completed ({len(results)} results)", flush=True)
    logger.info("Chroma retrieval completed; retrieved %d results", len(results))

    graph_result = await asyncio.to_thread(
        retrieve_from_graph,
        question,
    )

    print("RAG: Neo4j retrieval completed", flush=True)
    logger.info("Neo4j graph retrieval completed")

    chroma_context = build_context(results)

    graph_context = ""
    if graph_result.get("results"):
        graph_context = "\n".join(
            str(item)
            for item in graph_result["results"]
        )

    context = f"""
    VECTOR DATABASE RESULTS:
    {chroma_context}

    KNOWLEDGE GRAPH RESULTS:
    {graph_context}
    """

    print("RAG: combined Chroma + Neo4j context built", flush=True)
    logger.info("Combined vector and graph context built")

    prompt = f"""
        You are Nutrivault, an AI nutrition information assistant.

        Answer the user's question using ONLY the nutrition data
        provided in the context below.

        Rules:
        - Do not invent nutrition values.
        - Do not use nutrition facts that are not present in the context.
        - State only food and nutrient facts directly supported by a retrieved record.
        - Do not add general nutrition knowledge or combine values from different foods.
        - If the available data is insufficient, clearly say so.
        - Keep the answer concise and easy to understand.
        - Mention relevant food names and nutrition values when appropriate.
        - This is general nutrition information, not medical diagnosis or treatment.

        User question:
        {question}

        Retrieved nutrition data:
        {context}
        """

    print("RAG: calling Groq", flush=True)
    logger.info("Groq request started")
    answer = await generate_answer(prompt)
    if _has_unsupported_numbers(answer, context):
        logger.warning("LLM answer included values outside retrieved context; using retrieved facts")
        answer = _retrieved_facts_summary(results, graph_result)
    print("RAG: Groq returned", flush=True)
    logger.info("Groq request completed")

    return {
    "question": question,
    "answer": answer,
    "sources": [
        {
            "food_id": None,
            "food_name": result["food"],
            "food_type": None,
            "nutrition": {
                result["nutrient"]: result["value"]
            },
            "document": result["document"],
        }
        for result in results
    ],
    "graph_context": graph_result,
    "retrieval_metadata": {
        "retrieval_method": "chromadb",
        "top_k": len(results),
        "nutrient": results[0]["nutrient"] if results else None
    }
}
