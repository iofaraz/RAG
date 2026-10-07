"""
Integration tests against a REAL Neo4j. Skipped automatically if NEO4J_PASSWORD
is not set or the server is unreachable.

WARNING: these tests build the graph (MERGE only - nothing is deleted) into the
database configured by NEO4J_*. Point them at a dev database.

    pytest graph/tests/test_integration.py -v
"""
import pytest

from graph import schema
from graph.category_resolver import resolve_categories
from graph.graph_builder import build_graph, graph_counts
from graph.graph_retriever import GraphRetriever
from graph.seed_knowledge import GOALS, SUPPORTS


@pytest.fixture(scope="module")
def built(df):
    try:
        driver, settings = schema.get_driver()
    except Exception as e:  # no password, server down, bad auth ...
        pytest.skip(f"Neo4j not available: {e}")
    cats = resolve_categories(df, schema.RAW_DIR)
    first = build_graph(driver, settings.database, df, cats)
    yield driver, settings, first, cats
    driver.close()


@pytest.fixture(scope="module")
def r(built):
    driver, settings, *_ = built
    return GraphRetriever(driver, settings.database)


def q1(built, cypher, **p):
    driver, settings, *_ = built
    records, _, _ = driver.execute_query(cypher, p, database_=settings.database)
    return [x.data() for x in records]


# ------------------------------------------------------------- build correctness
def test_node_and_relationship_counts(built, df):
    _, _, counts, cats = built
    expected_contains = int(df[[n.column for n in schema.NUTRIENTS]].notna().sum().sum())
    assert counts["(:Food)"] == len(df)
    assert counts["(:Nutrient)"] == len(schema.NUTRIENTS)
    assert counts["(:Goal)"] == len(GOALS)
    assert counts["[:CONTAINS]"] == expected_contains
    assert counts["[:BELONGS_TO]"] == len(cats)
    assert counts["[:SUPPORTS]"] == len(SUPPORTS)


def test_rebuild_creates_no_duplicates(built, df):
    driver, settings, first, cats = built
    second = build_graph(driver, settings.database, df, cats)
    assert second == first


def test_no_duplicate_relationships(built):
    assert q1(built, "MATCH (f:Food)-[r:CONTAINS]->(n) WITH f, n, count(r) AS c WHERE c > 1 RETURN count(*) AS bad")[0]["bad"] == 0
    assert q1(built, "MATCH (f:Food)-[r:BELONGS_TO]->() WITH f, count(r) AS c WHERE c > 1 RETURN count(*) AS bad")[0]["bad"] == 0


def test_missing_nutrient_values_create_no_relationship(built, df):
    fdc = int(df[df.vitamin_d_ug.isna()].fdc_id.iloc[0])
    rows = q1(built, "MATCH (:Food {fdc_id: $id})-[r:CONTAINS]->(:Nutrient {key:'vitamin_d'}) RETURN r", id=fdc)
    assert rows == []


def test_amount_and_unit_preserved(built, df):
    row = df[df.protein_g.notna()].iloc[0]
    got = q1(built, "MATCH (:Food {fdc_id: $id})-[r:CONTAINS]->(:Nutrient {key:'protein'}) RETURN r.amount AS a, r.unit AS u",
             id=int(row.fdc_id))
    assert got == [{"a": float(row.protein_g), "u": "g"}]


def test_usda_and_curated_data_are_separated(built):
    assert q1(built, "MATCH ()-[r:CONTAINS]->() WHERE r.curated IS NOT NULL RETURN count(r) AS c")[0]["c"] == 0
    assert q1(built, "MATCH ()-[r:SUPPORTS]->() WHERE r.curated IS NULL OR r.source <> 'manual_curation' RETURN count(r) AS c")[0]["c"] == 0


# ------------------------------------------------------------- the 5 query types
def test_food_to_nutrients(r):
    res = r.retrieve("What nutrients does salmon contain?")
    assert res["intent"] == "food_nutrients" and res["results"]
    assert any(x["nutrient"] == "Protein" and x["unit"] == "g" for x in res["results"])


def test_nutrient_to_foods(r):
    res = r.retrieve("What foods contain protein?")
    amts = [x["amount"] for x in res["results"]]
    assert res["intent"] == "nutrient_foods" and amts and amts == sorted(amts, reverse=True)


def test_food_to_category(r):
    res = r.retrieve("What category does salmon belong to?")
    assert res["intent"] == "food_category" and all(x["category"] for x in res["results"])


def test_goal_to_nutrients(r):
    res = r.retrieve("What nutrients are associated with bone health?")
    assert {x["nutrient_key"] for x in res["results"]} == {"calcium", "vitamin_d", "magnesium"}


def test_multi_hop_food_nutrient_goal(r):
    res = r.retrieve("What foods contain nutrients associated with bone health?")
    assert res["intent"] == "goal_foods" and res["results"]
    assert {x["nutrient_key"] for x in res["results"]} <= {"calcium", "vitamin_d", "magnesium"}


# ------------------------------------------------------------- robustness
def test_unknown_food_does_not_crash(r):
    res = r.retrieve("What nutrients does flibbertigibbet contain?")
    assert res["results"] == [] and res["confidence"] == "none"


@pytest.mark.parametrize("q", ["What is the capital of France?", "hello", "", "Who won the world cup?"])
def test_unknown_question_returns_nothing(r, q):
    assert r.retrieve(q)["results"] == []
