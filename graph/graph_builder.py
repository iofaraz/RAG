"""
Build the Neo4j knowledge graph from food_nutrition_clean.csv.

    python -m graph.graph_builder                     # build / update (idempotent)
    python -m graph.graph_builder --reset             # wipe the 4 graph labels first
    python -m graph.graph_builder --inspect-categories  # no Neo4j needed

Run from the project root. Safe to run repeatedly: every write is a MERGE on a
uniquely-constrained key, so re-running never creates duplicate nodes or
relationships.
"""
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

from . import schema
from .category_resolver import coverage_report, resolve_categories
from .seed_knowledge import seed_knowledge

log = logging.getLogger("graph_builder")

# ---------------------------------------------------------------- pure functions
def load_foods(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    for col in ("fdc_id", "data_type", "food_name"):
        if col not in df.columns:
            raise ValueError(f"{csv_path} is missing required column '{col}'")
    if df["fdc_id"].duplicated().any():
        raise ValueError("duplicate fdc_id values in CSV")
    unmapped = [c for c in df.columns
                if re.search(r"_(g|mg|ug|kcal)$", c) and c not in schema.NUTRIENT_BY_COLUMN]
    if unmapped:
        log.warning("CSV nutrient columns with no mapping in schema.NUTRIENTS (ignored): %s", unmapped)
    return df


def build_food_rows(df: pd.DataFrame) -> list[dict]:
    return [
        {"fdc_id": int(r.fdc_id), "name": str(r.food_name), "name_lower": str(r.food_name).lower(),
         "data_type": str(r.data_type), "source": schema.USDA_SOURCE}
        for r in df.itertuples(index=False)
    ]


def build_contains_rows(df: pd.DataFrame) -> list[dict]:
    """One row per (food, nutrient) that HAS a value. Missing (NaN) -> no row.
    A genuine 0 is kept: 'USDA says 0' is information, 'unknown' is not."""
    rows: list[dict] = []
    for nd in schema.NUTRIENTS:
        if nd.column not in df.columns:
            log.warning("Column %s not in CSV - nutrient %s skipped", nd.column, nd.key)
            continue
        s = df[["fdc_id", nd.column]].dropna()
        s = s[s[nd.column] >= 0]                        # defensive; CSV is already validated
        rows.extend(
            {"fdc_id": int(i), "nutrient": nd.key, "amount": float(v), "unit": nd.unit}
            for i, v in zip(s["fdc_id"], s[nd.column])
        )
    return rows


# ---------------------------------------------------------------- Cypher writers
Q_NUTRIENTS = """
UNWIND $rows AS row
MERGE (n:Nutrient {key: row.key})
SET n.name = row.name, n.unit = row.unit, n.csv_column = row.column,
    n.sort_order = row.sort_order, n.source = $source
"""
Q_FOODS = """
UNWIND $rows AS row
MERGE (f:Food {fdc_id: row.fdc_id})
SET f.name = row.name, f.name_lower = row.name_lower,
    f.data_type = row.data_type, f.source = row.source
"""
Q_CONTAINS = """
UNWIND $rows AS row
MATCH (f:Food {fdc_id: row.fdc_id})
MATCH (n:Nutrient {key: row.nutrient})
MERGE (f)-[r:CONTAINS]->(n)
SET r.amount = row.amount, r.unit = row.unit, r.basis = $basis, r.source = $source
"""
Q_CATEGORIES = "UNWIND $rows AS row MERGE (:FoodCategory {name: row.name})"
Q_BELONGS_TO = """
UNWIND $rows AS row
MATCH (f:Food {fdc_id: row.fdc_id})
OPTIONAL MATCH (f)-[old:BELONGS_TO]->(:FoodCategory)
DELETE old
WITH f, row
MATCH (c:FoodCategory {name: row.category})
MERGE (f)-[r:BELONGS_TO]->(c)
SET r.category_source = row.category_source
"""


def _batched(session, query, rows, size, label, **params):
    total = len(rows)
    for i in range(0, total, size):
        batch = rows[i:i + size]
        session.execute_write(lambda tx, b=batch: tx.run(query, rows=b, **params).consume())
        log.info("  %s: %d / %d", label, min(i + size, total), total)


def reset_graph(session) -> None:
    for label in (schema.FOOD, schema.NUTRIENT, schema.CATEGORY, schema.GOAL):
        while True:
            n = session.run(f"MATCH (n:{label}) WITH n LIMIT 5000 DETACH DELETE n RETURN count(*) AS c").single()["c"]
            if n == 0:
                break
        log.info("  cleared :%s", label)


def graph_counts(session) -> dict:
    out = {}
    for label in (schema.FOOD, schema.NUTRIENT, schema.CATEGORY, schema.GOAL):
        out[f"(:{label})"] = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
    for rel in (schema.CONTAINS, schema.BELONGS_TO, schema.SUPPORTS):
        out[f"[:{rel}]"] = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
    return out


def build_graph(driver, database, df, categories, batch_size=2000, reset=False) -> dict:
    with driver.session(database=database) as session:
        if reset:
            log.info("Resetting graph labels ...")
            reset_graph(session)

        log.info("Creating constraints ...")
        for stmt in schema.CONSTRAINTS:
            session.run(stmt).consume()

        log.info("Nutrient nodes ...")
        nutrient_rows = [
            {"key": n.key, "name": n.name, "unit": n.unit, "column": n.column, "sort_order": i}
            for i, n in enumerate(schema.NUTRIENTS)
        ]
        session.execute_write(lambda tx: tx.run(Q_NUTRIENTS, rows=nutrient_rows, source=schema.USDA_SOURCE).consume())

        log.info("Food nodes ...")
        _batched(session, Q_FOODS, build_food_rows(df), batch_size, "foods")

        log.info("CONTAINS relationships ...")
        _batched(session, Q_CONTAINS, build_contains_rows(df), batch_size * 3, "contains",
                 basis=schema.AMOUNT_BASIS, source=schema.USDA_SOURCE)

        log.info("FoodCategory nodes + BELONGS_TO ...")
        cat_names = sorted({c for c, _ in categories.values()})
        _batched(session, Q_CATEGORIES, [{"name": c} for c in cat_names], batch_size, "categories")
        belongs = [{"fdc_id": f, "category": c, "category_source": s} for f, (c, s) in categories.items()]
        _batched(session, Q_BELONGS_TO, belongs, batch_size, "belongs_to")

        log.info("Curated Goal layer ...")
        seed_knowledge(session)

        return graph_counts(session)


# ---------------------------------------------------------------- CLI
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, default=schema.DEFAULT_CSV)
    ap.add_argument("--raw-dir", type=Path, default=schema.RAW_DIR, help="folder with food.csv, food_category.csv, ...")
    ap.add_argument("--category-fallback", choices=["name-prefix", "none"], default="name-prefix")
    ap.add_argument("--batch-size", type=int, default=2000)
    ap.add_argument("--reset", action="store_true", help="delete existing Food/Nutrient/FoodCategory/Goal nodes first")
    ap.add_argument("--inspect-categories", action="store_true", help="print category coverage and exit (no Neo4j)")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = load_foods(args.csv)
    log.info("Loaded %d foods from %s", len(df), args.csv)
    categories = resolve_categories(df, args.raw_dir, args.category_fallback)

    if args.inspect_categories:
        print(coverage_report(df, categories))
        return

    driver, settings = schema.get_driver()
    try:
        counts = build_graph(driver, settings.database, df, categories, args.batch_size, args.reset)
    finally:
        driver.close()
    print("\nGraph contents:")
    for k, v in counts.items():
        print(f"  {k:<18} {v}")


if __name__ == "__main__":
    main()
