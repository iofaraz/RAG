# backend/services/rag.py
"""Stand-in for Member 2's rag_pipeline.answer_query().

PROPOSED CONTRACT — confirm with Member 2:
    answer_query(query: str) -> dict
        returns {"answer": str, "sources": [{"name": str,
                 "detail": str | None, "score": float | None}]}
"""


def answer_query(query: str) -> dict:
    """Return a nutrition answer plus citation sources."""
    return {
        "answer": (
            "STUB DATA — bison and salmon are among the retrieved "
            "high-protein foods. Bison leads with 21.62 g of protein "
            "per 100 g."
        ),
        "sources": [
            {"name": "Game meat, bison", "detail": "21.62 g protein per 100g", "score": 0.98},
            {"name": "Fish, salmon, Atlantic", "detail": "20.32 g protein per 100g", "score": 0.95},
            {"name": "Beef, ground, bison", "detail": "19.88 g protein per 100g", "score": 0.93},
        ],
    }