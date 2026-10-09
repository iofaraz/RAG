# backend/schemas/query.py
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """What the frontend sends to us."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["What foods are high in protein?"],
    )


class Source(BaseModel):
    """One retrieved food item shown as a citation under the answer."""
    name: str
    detail: str | None = None      # e.g. "21.62 g protein per 100g"
    score: float | None = None     # rerank score, if the retriever gives one
    food_id: int | str | None = None
    food_type: str | None = None
    nutrition: dict = Field(default_factory=dict)
    basis: str | None = None
    source: str | None = None


class QueryResponse(BaseModel):
    """What we send back to the frontend."""
    query: str
    answer: str
    sources: list[Source] = Field(default_factory=list)
    graph_results: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)       # what failed, so the UI can show it
