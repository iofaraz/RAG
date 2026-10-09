import os
from pathlib import Path
import re

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_DIR = Path(
    os.getenv("CHROMA_DB_PATH", str(PROJECT_ROOT / "data" / "chroma_db"))
).expanduser()
if not DB_DIR.is_absolute():
    DB_DIR = PROJECT_ROOT / DB_DIR

model = None


def _get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

collection = None


def _get_collection():
    global collection
    if collection is None:
        client = chromadb.PersistentClient(path=str(DB_DIR))
        collection = client.get_collection(name="food_nutrition")
    return collection


NUTRIENT_PATTERNS = {
    "protein": r"protein|high protein|rich in protein",
    "calcium": r"calcium",
    "iron": r"iron",
    "vitamin c": r"vitamin c",
    "vitamin a": r"vitamin a",
    "vitamin d": r"vitamin d",
    "vitamin b6": r"vitamin b6",
    "vitamin b12": r"vitamin b12",
    "fiber": r"fiber|fibre",
    "fat": r"fat|fats",
    "carbohydrates": r"carbohydrate|carbohydrates|carbs",
    "sodium": r"sodium",
    "potassium": r"potassium",
    "magnesium": r"magnesium",
    "zinc": r"zinc",
    "sugar": r"sugar|sugars",
    "cholesterol": r"cholesterol",
    "calories": r"calorie|calories|energy"
}


DOCUMENT_LABELS = {
    "protein": "Protein",
    "calcium": "Calcium",
    "iron": "Iron",
    "vitamin c": "Vitamin C",
    "vitamin a": "Vitamin A",
    "vitamin d": "Vitamin D",
    "vitamin b6": "Vitamin B6",
    "vitamin b12": "Vitamin B12",
    "fiber": "Fiber",
    "fat": "Fat",
    "carbohydrates": "Carbohydrates",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "magnesium": "Magnesium",
    "zinc": "Zinc",
    "sugar": "Sugar",
    "cholesterol": "Cholesterol",
    "calories": "Calories"
}


def detect_nutrient(query):

    query_lower = query.lower()

    for nutrient, pattern in NUTRIENT_PATTERNS.items():

        if re.search(pattern, query_lower):
            return nutrient

    return None


def extract_value(document, label):

    pattern = rf"{re.escape(label)}:\s*([-+]?\d*\.?\d+)"

    match = re.search(pattern, document)

    if match:
        return float(match.group(1))

    return None


def extract_food_name(document):

    match = re.search(r"Food:\s*(.+)", document)

    if match:
        return match.group(1)

    return "Unknown"


def retrieve_foods(query, n_candidates=30, top_k=5):

    query_embedding = _get_model().encode(query).tolist()

    results = _get_collection().query(
        query_embeddings=[query_embedding],
        n_results=n_candidates
    )

    nutrient = detect_nutrient(query)

    foods = []

    for document in results["documents"][0]:

        food_name = extract_food_name(document)

        nutrient_value = None

        if nutrient:
            label = DOCUMENT_LABELS[nutrient]
            nutrient_value = extract_value(document, label)

        foods.append(
            {
                "food": food_name,
                "nutrient": nutrient,
                "value": nutrient_value,
                "document": document
            }
        )

    # If a nutrient was detected, remove foods
    # that do not contain that nutrient.
    if nutrient:

        foods = [
            food
            for food in foods
            if food["value"] is not None
        ]

        # Highest nutrient value first.
        foods.sort(
            key=lambda x: x["value"],
            reverse=True
        )

    return foods[:top_k]
