from retriever import retrieve_foods
from llm_client import generate_answer


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


def answer_question(question):

    results = retrieve_foods(question)

    context = build_context(results)

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

    answer = generate_answer(prompt)

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
    "graph_context": [],
    "retrieval_metadata": {
        "retrieval_method": "chromadb",
        "top_k": len(results),
        "nutrient": results[0]["nutrient"] if results else None
    }
}