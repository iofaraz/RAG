"""
Graph schema: labels, relationship types, constraints, the CSV -> Nutrient
mapping, and Neo4j connection settings.

Everything that defines "what the graph looks like" lives here so the builder
and the retriever can never disagree about it.

    (Food)-[:CONTAINS {amount, unit, basis}]->(Nutrient)      USDA-derived
    (Food)-[:BELONGS_TO {category_source}]->(FoodCategory)    USDA-derived (or labelled heuristic)
    (Nutrient)-[:SUPPORTS {basis, curated}]->(Goal)           manually curated
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_CSV = RAW_DIR / "food_nutrition_clean.csv"

try:  # optional convenience
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# ----------------------------------------------------------------- labels
FOOD, NUTRIENT, CATEGORY, GOAL = "Food", "Nutrient", "FoodCategory", "Goal"
CONTAINS, BELONGS_TO, SUPPORTS = "CONTAINS", "BELONGS_TO", "SUPPORTS"

USDA_SOURCE = "USDA FoodData Central"
AMOUNT_BASIS = "per 100 g"  # FDC SR Legacy / Foundation / FNDDS values are per 100 g of food

CONSTRAINTS = [
    "CREATE CONSTRAINT food_fdc_id IF NOT EXISTS FOR (f:Food) REQUIRE f.fdc_id IS UNIQUE",
    "CREATE CONSTRAINT nutrient_key IF NOT EXISTS FOR (n:Nutrient) REQUIRE n.key IS UNIQUE",
    "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:FoodCategory) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT goal_key IF NOT EXISTS FOR (g:Goal) REQUIRE g.key IS UNIQUE",
]


# --------------------------------------------------------- nutrient mapping
@dataclass(frozen=True)
class NutrientDef:
    column: str          # column in food_nutrition_clean.csv
    key: str             # stable slug (Nutrient.key)
    name: str            # display name
    unit: str            # unit as stored on the graph
    aliases: tuple = ()  # words a user might type (used by the retriever)


NUTRIENTS: list[NutrientDef] = [
    NutrientDef("calcium_mg", "calcium", "Calcium", "mg", ("calcium",)),
    NutrientDef("calories_kcal", "calories", "Calories", "kcal", ("calories", "calorie", "energy", "kcal")),
    NutrientDef("carbohydrates_g", "carbohydrates", "Carbohydrates", "g", ("carbohydrates", "carbohydrate", "carbs", "carb")),
    NutrientDef("cholesterol_mg", "cholesterol", "Cholesterol", "mg", ("cholesterol",)),
    NutrientDef("fat_g", "fat", "Fat", "g", ("fat", "total fat")),
    NutrientDef("fiber_g", "fiber", "Fiber", "g", ("fiber", "fibre", "dietary fiber", "dietary fibre")),
    NutrientDef("folate_ug", "folate", "Folate", "µg", ("folate", "folic acid")),
    NutrientDef("iron_mg", "iron", "Iron", "mg", ("iron",)),
    NutrientDef("magnesium_mg", "magnesium", "Magnesium", "mg", ("magnesium",)),
    NutrientDef("monounsaturated_fat_g", "monounsaturated_fat", "Monounsaturated Fat", "g", ("monounsaturated fat", "mufa")),
    NutrientDef("polyunsaturated_fat_g", "polyunsaturated_fat", "Polyunsaturated Fat", "g", ("polyunsaturated fat", "pufa")),
    NutrientDef("potassium_mg", "potassium", "Potassium", "mg", ("potassium",)),
    NutrientDef("protein_g", "protein", "Protein", "g", ("protein",)),
    NutrientDef("saturated_fat_g", "saturated_fat", "Saturated Fat", "g", ("saturated fat", "sat fat")),
    NutrientDef("sodium_mg", "sodium", "Sodium", "mg", ("sodium",)),
    NutrientDef("sugar_g", "sugar", "Sugar", "g", ("sugar",)),
    NutrientDef("trans_fat_g", "trans_fat", "Trans Fat", "g", ("trans fat",)),
    NutrientDef("vitamin_a_ug", "vitamin_a", "Vitamin A", "µg", ("vitamin a",)),
    NutrientDef("vitamin_b12_ug", "vitamin_b12", "Vitamin B12", "µg", ("vitamin b12", "vitamin b-12", "b12", "b-12", "cobalamin")),
    NutrientDef("vitamin_b6_mg", "vitamin_b6", "Vitamin B6", "mg", ("vitamin b6", "vitamin b-6", "b6", "b-6")),
    NutrientDef("vitamin_c_mg", "vitamin_c", "Vitamin C", "mg", ("vitamin c", "ascorbic acid")),
    NutrientDef("vitamin_d_ug", "vitamin_d", "Vitamin D", "µg", ("vitamin d",)),
    NutrientDef("vitamin_e_mg", "vitamin_e", "Vitamin E", "mg", ("vitamin e",)),
    NutrientDef("vitamin_k_ug", "vitamin_k", "Vitamin K", "µg", ("vitamin k",)),
    NutrientDef("zinc_mg", "zinc", "Zinc", "mg", ("zinc",)),
]
NUTRIENT_BY_KEY = {n.key: n for n in NUTRIENTS}
NUTRIENT_BY_COLUMN = {n.column: n for n in NUTRIENTS}


# ----------------------------------------------------------- connection
@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "Neo4jSettings":
        password = os.getenv("NEO4J_PASSWORD")
        if not password:
            raise RuntimeError(
                "NEO4J_PASSWORD is not set. Set NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD "
                "(and optionally NEO4J_DATABASE) as environment variables or in a .env file "
                "at the project root."
            )
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=password,
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )


def get_driver():
    """Return a verified neo4j.Driver (caller closes it). Returns (driver, settings)."""
    from neo4j import GraphDatabase

    settings = Neo4jSettings.from_env()
    driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))
    driver.verify_connectivity()
    return driver, settings
