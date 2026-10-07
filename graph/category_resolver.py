"""
Decide which FoodCategory each food belongs to.

food_nutrition_clean.csv has NO category column, so categories come from the
raw USDA tables, in this order of trust:

  1. usda_food_category : food.csv.food_category_id -> food_category.csv
                          (SR Legacy / Foundation foods)
  2. usda_wweia         : survey_fndds_food.csv -> wweia_food_category.csv
                          (FNDDS survey foods)
  3. derived_name_prefix: first comma-separated chunk of the food name
                          ("Fish, salmon, raw" -> "Fish"). A heuristic, used only
                          when 1 and 2 give nothing. Always labelled as such.

Every BELONGS_TO relationship stores its `category_source`, so the retriever
(and your demo) can always say where a category came from.

Column names in the raw tables are looked up defensively; if a raw file is
missing or shaped differently, that step is skipped (with a warning) and the
next step takes over. Run `python -m graph.graph_builder --inspect-categories`
to see exactly what you got before building the graph.
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

SRC_FOOD_CATEGORY = "usda_food_category"
SRC_WWEIA = "usda_wweia"
SRC_NAME_PREFIX = "derived_name_prefix"


def _find_col(columns, *needles):
    """First column whose lowercase name contains any needle (in needle order)."""
    for needle in needles:
        for c in columns:
            if needle in c.lower():
                return c
    return None


def _read(path: Path, usecols=None) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, usecols=usecols)


def _usda_food_categories(raw_dir: Path, wanted: set[str]) -> dict[int, str]:
    food_p, cat_p = raw_dir / "food.csv", raw_dir / "food_category.csv"
    if not (food_p.exists() and cat_p.exists()):
        log.warning("food.csv / food_category.csv not found in %s - skipping USDA categories", raw_dir)
        return {}
    food = _read(food_p, usecols=lambda c: c in ("fdc_id", "food_category_id"))
    if "food_category_id" not in food.columns:
        log.warning("food.csv has no food_category_id column - skipping")
        return {}
    cats = _read(cat_p)
    desc = _find_col(cats.columns, "description", "name")
    if desc is None:
        log.warning("food_category.csv has no description column - skipping")
        return {}
    by_id = dict(zip(cats["id"], cats[desc])) if "id" in cats.columns else {}
    by_code = dict(zip(cats["code"], cats[desc])) if "code" in cats.columns else {}

    out = {}
    for fdc_id, raw in zip(food["fdc_id"], food["food_category_id"]):
        if fdc_id not in wanted or not raw.strip():
            continue
        v = raw.strip()
        if v in by_id:
            out[int(fdc_id)] = by_id[v]
        elif v in by_code:
            out[int(fdc_id)] = by_code[v]
        elif not v.isdigit():          # some releases store the category text directly
            out[int(fdc_id)] = v
    return out


def _wweia_categories(raw_dir: Path, wanted: set[str]) -> dict[int, str]:
    sv_p, w_p = raw_dir / "survey_fndds_food.csv", raw_dir / "wweia_food_category.csv"
    if not (sv_p.exists() and w_p.exists()):
        log.warning("survey_fndds_food.csv / wweia_food_category.csv not found - skipping WWEIA categories")
        return {}
    sv, w = _read(sv_p), _read(w_p)
    sv_col = _find_col(sv.columns, "wweia")
    w_id = _find_col(w.columns, "code", "id")
    w_desc = _find_col(w.columns, "description")
    if not (sv_col and w_id and w_desc and "fdc_id" in sv.columns):
        log.warning("Unexpected WWEIA table layout (%s / %s) - skipping", list(sv.columns), list(w.columns))
        return {}
    lookup = dict(zip(w[w_id], w[w_desc]))
    out = {}
    for fdc_id, code in zip(sv["fdc_id"], sv[sv_col]):
        if fdc_id in wanted and code in lookup:
            out[int(fdc_id)] = lookup[code]
    return out


def name_prefix_category(food_name: str) -> str:
    return food_name.split(",")[0].strip().title() or "Uncategorized"


def resolve_categories(df: pd.DataFrame, raw_dir: Path, fallback: str = "name-prefix") -> dict[int, tuple[str, str]]:
    """Return {fdc_id: (category_name, category_source)} for every food in df.

    fallback = "name-prefix" -> unresolved foods get a heuristic category
               "none"        -> unresolved foods get no category at all
    """
    wanted = {str(i) for i in df["fdc_id"]}
    result: dict[int, tuple[str, str]] = {}
    for fdc_id, cat in _usda_food_categories(raw_dir, wanted).items():
        result[fdc_id] = (cat, SRC_FOOD_CATEGORY)
    for fdc_id, cat in _wweia_categories(raw_dir, wanted).items():
        result.setdefault(fdc_id, (cat, SRC_WWEIA))
    if fallback == "name-prefix":
        for fdc_id, name in zip(df["fdc_id"], df["food_name"]):
            result.setdefault(int(fdc_id), (name_prefix_category(name), SRC_NAME_PREFIX))
    return result


def coverage_report(df: pd.DataFrame, mapping: dict[int, tuple[str, str]]) -> str:
    lines = [f"Foods: {len(df)}   with a category: {len(mapping)}   without: {len(df) - len(mapping)}", ""]
    by_dt = Counter()
    for fdc_id, dt in zip(df["fdc_id"], df["data_type"]):
        src = mapping.get(int(fdc_id), (None, "NONE"))[1]
        by_dt[(dt, src)] += 1
    lines.append("data_type x category_source")
    for (dt, src), n in sorted(by_dt.items()):
        lines.append(f"  {dt:<20} {src:<22} {n}")
    cats = Counter(c for c, _ in mapping.values())
    lines += ["", f"Distinct categories: {len(cats)}", "Top 15:"]
    lines += [f"  {n:>5}  {c}" for c, n in cats.most_common(15)]
    return "\n".join(lines)
