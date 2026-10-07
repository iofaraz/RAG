# backend/app/main.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas.query import QueryRequest, QueryResponse, Source
from backend.services.graph import retrieve_from_graph
from backend.services.rag import answer_query

app = FastAPI(title="Nutrition RAG Backend")

# --- CORS: lets Member 4's Next.js talk to you ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health check: confirm the server works ---
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "nutrition-rag-backend"}

# --- Main query endpoint: the heart of the API ---
@app.post("/api/query", response_model=QueryResponse)
def query(body: QueryRequest):
    rag = answer_query(body.query)            # Member 2's pipeline (stub)
    graph = retrieve_from_graph(body.query)   # Member 1's graph (stub)

    return QueryResponse(
        query=body.query,
        answer=rag["answer"],
        sources=[Source(**s) for s in rag["sources"]],
        graph_results=graph,
    )