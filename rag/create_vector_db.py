from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# Paths
PROJECT_ROOT = Path(
    r"D:\University Projects\3rd Semester\Software Engineering\RAG"
)

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "rag_documents"
DB_DIR = PROJECT_ROOT / "data" / "chroma_db"

# Load embedding model
print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded.")

# Create ChromaDB
client = chromadb.PersistentClient(
    path=str(DB_DIR)
)

collection = client.get_or_create_collection(
    name="food_nutrition"
)

# Read documents
documents = []
ids = []

files = sorted(DOCUMENTS_DIR.glob("*.txt"))

print(f"Documents found: {len(files):,}")

for file in files:
    documents.append(
        file.read_text(encoding="utf-8")
    )

    ids.append(file.stem)

# Add documents in batches
batch_size = 500

for start in range(0, len(documents), batch_size):

    end = start + batch_size

    batch_documents = documents[start:end]
    batch_ids = ids[start:end]

    print(
        f"Embedding documents {start + 1:,} "
        f"to {min(end, len(documents)):,}..."
    )

    embeddings = model.encode(
        batch_documents,
        show_progress_bar=True
    ).tolist()

    collection.add(
        ids=batch_ids,
        documents=batch_documents,
        embeddings=embeddings
    )

print("\n" + "=" * 70)
print("VECTOR DATABASE CREATED")
print("=" * 70)

print(f"Documents stored: {collection.count():,}")
print(f"Database location: {DB_DIR}")