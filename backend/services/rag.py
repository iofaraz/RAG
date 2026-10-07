# backend/services/rag.py

from rag.rag_pipeline import answer_question


def answer_query(query: str) -> dict:
    """Run the real RAG pipeline and adapt its response for the backend."""

    result = answer_question(query)

    sources = []

    for source in result.get("sources", []):
        nutrition = source.get("nutrition", {})

        detail = None
        if nutrition:
            nutrient, value = next(iter(nutrition.items()))
            if value is not None:
                detail = f"{value} {nutrient}"

        sources.append(
            {
                "name": source.get("food_name", "Unknown food"),
                "detail": detail,
                "score": None,
            }
        )

    return {
        "answer": result.get("answer", ""),
        "sources": sources,
    }