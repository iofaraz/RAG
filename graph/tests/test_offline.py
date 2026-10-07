"""Tests that need neither Neo4j nor the raw USDA tables. Run: pytest graph/tests -v"""
import json
import math

import pandas as pd
import pytest

from graph import schema
from graph.category_resolver import SRC_FOOD_CATEGORY, SRC_NAME_PREFIX, SRC_WWEIA, resolve_categories
from graph.graph_builder import build_contains_rows, build_food_rows
from graph.seed_knowledge import GOAL_BY_KEY, SUPPORTS
from fake_backend import FakeRetriever


@pytest.fixture(scope="module")
def r(df, tmp_path_factory):
    return FakeRetriever(df, tmp_path_factory.mktemp("raw"))   # empty raw dir -> name-prefix categories


# ---------------------------------------------------------------- schema / builder rows
def test_every_csv_nutrient_column_is_mapped(df):
    cols = [c for c in df.columns if c.endswith(("_g", "_mg", "_ug", "_kcal"))]
    assert sorted(cols) == sorted(schema.NUTRIENT_BY_COLUMN)
    assert len(schema.NUTRIENTS) == 25


def test_units_match_csv_suffix():
    expect = {"g": "g", "mg": "mg", "ug": "µg", "kcal": "kcal"}
    for n in schema.NUTRIENTS:
        assert n.unit == expect[n.column.rsplit("_", 1)[1]], n


def test_contains_rows_skip_missing_and_keep_values(df):
    rows = build_contains_rows(df)
    assert len(rows) == int(df[[n.column for n in schema.NUTRIENTS]].notna().sum().sum())
    assert not any(math.isnan(x["amount"]) for x in rows)
    # no duplicates of (food, nutrient)
    assert len({(x["fdc_id"], x["nutrient"]) for x in rows}) == len(rows)
    # a food with NaN vitamin D must have no vitamin_d row
    missing = int(df[df.vitamin_d_ug.isna()].fdc_id.iloc[0])
    assert not any(x["fdc_id"] == missing and x["nutrient"] == "vitamin_d" for x in rows)
    # exact value preserved
    one = df[df.protein_g.notna()].iloc[0]
    assert any(x["fdc_id"] == int(one.fdc_id) and x["nutrient"] == "protein"
               and x["amount"] == float(one.protein_g) and x["unit"] == "g" for x in rows)


def test_food_rows_unique_and_complete(df):
    rows = build_food_rows(df)
    assert len(rows) == len(df) == len({x["fdc_id"] for x in rows})


def test_curated_links_reference_real_nutrients_and_goals():
    for n, g, basis in SUPPORTS:
        assert n in schema.NUTRIENT_BY_KEY and g in GOAL_BY_KEY and basis.endswith(".")
    assert len(SUPPORTS) == len(set((n, g) for n, g, _ in SUPPORTS))


# ---------------------------------------------------------------- category resolver
def test_category_resolver_usda_then_wweia_then_prefix(tmp_path):
    (tmp_path / "food.csv").write_text("fdc_id,data_type,description,food_category_id\n1,sr_legacy_food,x,1\n2,survey_fndds_food,y,\n3,foundation_food,z,\n")
    (tmp_path / "food_category.csv").write_text("id,code,description\n1,0100,Dairy and Egg Products\n")
    (tmp_path / "survey_fndds_food.csv").write_text("id,fdc_id,food_code,wweia_category_code\n9,2,1000,1004\n")
    (tmp_path / "wweia_food_category.csv").write_text("wweia_food_category_code,wweia_food_category_description\n1004,Cheese\n")
    df = pd.DataFrame({"fdc_id": [1, 2, 3], "food_name": ["Milk, whole", "Cheddar", "Fish, salmon, raw"],
                       "data_type": ["sr_legacy_food", "survey_fndds_food", "foundation_food"]})
    m = resolve_categories(df, tmp_path)
    assert m[1] == ("Dairy and Egg Products", SRC_FOOD_CATEGORY)
    assert m[2] == ("Cheese", SRC_WWEIA)
    assert m[3] == ("Fish", SRC_NAME_PREFIX)
    assert 3 not in resolve_categories(df, tmp_path, "none")


# ---------------------------------------------------------------- retriever: the 5 required query types
def test_1_food_to_nutrients(r):
    res = r.retrieve("What nutrients does salmon contain?")
    assert res["intent"] == "food_nutrients" and res["results"]
    assert all("salmon" in x["food"].lower() and x["relationship"] == "CONTAINS" for x in res["results"])
    prot = [x for x in res["results"] if x["nutrient_key"] == "protein"][0]
    assert prot["unit"] == "g" and prot["amount"] > 10
    json.dumps(res)  # serialisable


def test_food_nutrient_amount(r):
    res = r.retrieve("How much protein does salmon contain?")
    assert res["intent"] == "food_nutrient_amount"
    assert {x["nutrient_key"] for x in res["results"]} == {"protein"}


def test_2_nutrient_to_foods(r):
    res = r.retrieve("What foods contain protein?")
    amts = [x["amount"] for x in res["results"]]
    assert res["intent"] == "nutrient_foods" and len(amts) == 10 and amts == sorted(amts, reverse=True)


def test_3_food_to_category(r):
    res = r.retrieve("What category does salmon belong to?")
    assert res["intent"] == "food_category" and res["results"]
    assert all(x["relationship"] == "BELONGS_TO" and x["category"] for x in res["results"])


def test_4_goal_to_nutrients(r):
    res = r.retrieve("What nutrients are associated with bone health?")
    assert res["intent"] == "goal_nutrients"
    assert {x["nutrient_key"] for x in res["results"]} == {"calcium", "vitamin_d", "magnesium"}
    assert all(x["curated"] is True for x in res["results"])


def test_5_multi_hop_food_nutrient_goal(r):
    res = r.retrieve("What foods contain nutrients associated with bone health?")
    assert res["intent"] == "goal_foods" and res["results"]
    assert {x["nutrient_key"] for x in res["results"]} == {"calcium", "vitamin_d", "magnesium"}
    assert all("SUPPORTS" in x["relationship"] and x["amount"] > 0 for x in res["results"])


def test_category_to_foods(r):
    res = r.retrieve("What foods are in the Fish category?")
    assert res["intent"] == "category_foods" and res["results"]


# ---------------------------------------------------------------- robustness
@pytest.mark.parametrize("q", [
    "What is the capital of France?", "Who won the world cup?", "hello", "", "   ", "???",
    "What nutrients does flibbertigibbet contain?", "How much protein does unicorn steak have?",
    "What category does xyzzyfood belong to?",
])
def test_unknown_or_unsupported_questions_return_nothing(r, q):
    res = r.retrieve(q)
    assert res["results"] == [] and res["confidence"] == "none"
    json.dumps(res)


def test_non_string_query_does_not_crash(r):
    assert r.retrieve(None)["results"] == []


def test_ambiguous_food_is_low_confidence(r):
    res = r.retrieve("What nutrients does salmon contain?")
    assert res["confidence"] == "low" and any("match" in n for n in res["notes"])


def test_multiple_nutrients(r):
    res = r.retrieve("foods high in iron and zinc")
    assert {x["nutrient_key"] for x in res["results"]} == {"iron", "zinc"}


def test_alias_resolution(r):
    assert r.retrieve("foods rich in vitamin B-12")["entities"]["nutrients"] == ["vitamin_b12"]
    assert r.retrieve("foods high in saturated fat")["entities"]["nutrients"] == ["saturated_fat"]  # not plain "fat"
