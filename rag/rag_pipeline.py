import asyncio
import logging

from .retriever import retrieve_foods
from .llm_client import generate_answer
from graph.graph_retriever import retrieve_from_graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        - If the available data is insufficient, clearly say so.
        - Keep the answer concise and easy to understand.
        - Mention relevant food names and nutrition values when appropriate.
        - This is general nutrition information, not medical diagnosis or treatment.

        User question:
        {question}

        Retrieved nutrition data:
        {context}
        """

    print("RAG: calling Gemini", flush=True)
    logger.info("Gemini request started")
    answer = await generate_answer(prompt)
    print("RAG: Gemini returned", flush=True)
    logger.info("Gemini request completed")

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
            }
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