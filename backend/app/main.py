# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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