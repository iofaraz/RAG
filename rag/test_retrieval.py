from pathlib import Path
import re

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(
    r"D:\University Projects\3rd Semester\Software Engineering\RAG"
)

DB_DIR = PROJECT_ROOT / "data" / "chroma_db"


model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(
    path=str(DB_DIR)
)

collection = client.get_collection(
    name="food_nutrition"
)


def extract_value(document, label):
    pattern = rf"{re.escape(label)}:\s*([-+]?\d*\.?\d+)"
    match = re.search(pattern, document)

    if match:
        return float(match.group(1))

    return None


def search_protein_foods(query, n_candidates=30, top_k=5):

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_candidates
    )

    candidates = []

    for document in results["documents"][0]:

        protein = extract_value(document, "Protein")

        if protein is not None:
            food_match = re.search(
                r"Food:\s*(.+)",
                document
            )

            food_name = (
                food_match.group(1)
                if food_match
                else "Unknown"
            )

            candidates.append(
                {
                    "food": food_name,
                    "protein": protein,
                    "document": document
                }
            )

    candidates.sort(
        key=lambda x: x["protein"],
        reverse=True
    )

    return candidates[:top_k]


if __name__ == "__main__":

    query = "What foods are high in protein?"

    results = search_protein_foods(query)

    print("\n" + "=" * 70)
    print("TOP PROTEIN FOODS")
    print("=" * 70)

    for i, result in enumerate(results, start=1):

        print(
            f"{i}. {result['food']} "
            f"— {result['protein']} g protein"
        )