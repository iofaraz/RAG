import re

from rag.rag_pipeline import answer_question


async def answer_query(query: str) -> dict:
    result = await answer_question(query)

    sources = []
    seen_sources = set()

    for source in result.get("sources", []):
        nutrition = source.get("nutrition") or {}
        detail = None

        if nutrition:
            nutrient, value = next(iter(nutrition.items()))
            if value is not None:
                document = source.get("document", "")
                match = re.search(
                    rf"^\s*{re.escape(nutrient)}\s*:\s*([-+]?\d*\.?\d+)\s*(\S+)",
                    document,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
                if match:
                    detail = f"{match.group(1)} {match.group(2)} {nutrient}"
                else:
                    detail = f"{value} {nutrient}"

        name = source.get("food_name") or "Unknown food"
        key = (
            " ".join(str(name).split()).casefold(),
            " ".join(str(detail).split()).casefold() if detail is not None else None,
        )
        if key in seen_sources:
            continue
        seen_sources.add(key)

        sources.append({"name": name, "detail": detail, "score": None})

    return {
        "answer": result.get("answer", ""),
        "sources": sources,
        "graph_results": result.get("graph_context", {}),
    }
