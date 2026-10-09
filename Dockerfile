FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROMA_DB_PATH=/app/data/chroma_db

WORKDIR /app

# Copy only the application code and the existing persistent Chroma database.
# Root-level .env and frontend files are intentionally excluded.
COPY backend/ ./backend/
COPY rag/ ./rag/
COPY graph/ ./graph/
COPY data/chroma_db/ ./data/chroma_db/

# Neo4j's driver is declared in graph/requirements.txt rather than the backend
# requirements, but is needed by the backend's graph retrieval at runtime.
RUN pip install --no-cache-dir -r backend/requirements.txt "neo4j>=5.20"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
