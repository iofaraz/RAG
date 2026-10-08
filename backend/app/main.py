# backend/app/main.py
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas.query import QueryRequest, QueryResponse, Source
from backend.services.graph import retrieve_from_graph
from backend.services.rag import answer_query
from rag.llm_client import LLMRequestTimeout, LLMServiceError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
RAG_REQUEST_TIMEOUT_SECONDS = 20
GRAPH_REQUEST_TIMEOUT_SECONDS = 5

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
async def query(body: QueryRequest):
    print("API: query started", flush=True)
    logger.info("Query request started")
    # RAG side (Member 2) — without it there is no answer
    try:
        rag = await asyncio.wait_for(
            answer_query(body.query),
            timeout=RAG_REQUEST_TIMEOUT_SECONDS,
        )
        answer = rag["answer"]
        sources = [Source(**s) for s in rag["sources"]]
        warnings = []
    except LLMRequestTimeout as exc:
        logger.exception("LLM request timed out")
        raise HTTPException(
            status_code=504,
            detail="The LLM request timed out. Please try again.",
        ) from exc
    except LLMServiceError as exc:
        logger.exception("LLM service request failed")
        raise HTTPException(
            status_code=503,
            detail="The nutrition answer service is temporarily unavailable. Please try again shortly.",
        ) from exc
    except asyncio.TimeoutError as exc:
        logger.exception(
            "RAG request exceeded its %s-second deadline",
            RAG_REQUEST_TIMEOUT_SECONDS,
        )
        raise HTTPException(
            status_code=504,
            detail=f"RAG request timed out after {RAG_REQUEST_TIMEOUT_SECONDS} seconds.",
        ) from exc
    except Exception as exc:
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=502,
            detail="The nutrition service could not complete your request. Please try again shortly.",
        ) from exc

    # Graph side (Member 1) — enrichment; degrade gracefully
    print("API: RAG completed; starting graph enrichment", flush=True)
    try:
        graph = await asyncio.wait_for(
            asyncio.to_thread(retrieve_from_graph, body.query),
            timeout=GRAPH_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.exception(
            "Graph retrieval exceeded its %s-second deadline",
            GRAPH_REQUEST_TIMEOUT_SECONDS,
        )
        graph = []
        warnings.append(
            f"Knowledge graph retrieval timed out after "
            f"{GRAPH_REQUEST_TIMEOUT_SECONDS} seconds; answer uses vector retrieval only."
        )
    except Exception as exc:
        logger.exception("Graph retriever failed")
        graph = []
        warnings.append(
            f"Knowledge graph unavailable: {exc}; answer uses vector retrieval only."
        )

    print("API: query completed", flush=True)
    return QueryResponse(
        query=body.query,
        answer=answer,
        sources=sources,
        graph_results=graph,
        warnings=warnings,
    )
