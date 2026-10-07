"""
Graph retrieval over the Neo4j knowledge graph.

    from graph.graph_retriever import retrieve_from_graph
    retrieve_from_graph("What nutrients does salmon contain?")

Design: a tiny rule-based parser finds entities (nutrients, goals, categories,
a food phrase) and picks one of 7 intents; Cypher does ALL the actual
retrieval. If nothing in the question can be tied to something that exists in
the graph, the result is empty with confidence "none" - never a guess.

Response envelope (always the same keys, always JSON-serialisable):

    {
      "query": str,
      "intent": "food_nutrients" | "food_nutrient_amount" | "nutrient_foods" |
                "food_category" | "category_foods" | "goal_nutrients" |
                "goal_foods" | "unknown",
      "confidence": "high" | "low" | "none",
      "entities": {"food_term", "foods", "nutrients", "goals", "categories"},
      "results": [ {... "relationship": "CONTAINS" | "BELONGS_TO" | "SUPPORTS" | path ...} ],
      "notes": [str]
    }

confidence: "high"  = intent understood and every entity resolved in the graph
            "low"   = answered, but the food phrase was ambiguous (we used the best few matches)
            "none"  = nothing could be grounded in the graph; results == []
"""
from __future__ import annotations

import json
import re
import sys

from . import schema
from .seed_knowledge import GOALS

# ------------------------------------------------------------------ vocabulary
STOPWORDS = set("""
a an the of in on at to for with and or from by as is are was were be been do does did has have had
what which who whom whose how why when where much many more most some any all
tell me show give list find get name please can could would should i we you it its
food foods nutrient nutrients nutrition nutritional vitamin vitamins mineral minerals
contain contains containing contained high higher rich richest source sources good best great
amount amounts content level levels per gram grams g mg ug kcal serving
category categories belong belongs belonging type kind group class classified
associated association support supports supporting help helps related relate relates linked
eat eating meal meals diet that these those there their them
""".split())

FOOD_WORDS = {"food", "foods", "eat", "eating", "meal", "meals", "diet"}
CATEGORY_WORDS = {"category", "categories", "belong", "belongs", "belonging", "type", "kind", "group", "class", "classified"}
NUTRIENT_LIST_WORDS = {"nutrient", "nutrients", "nutrition", "nutritional", "vitamin", "vitamins", "mineral", "minerals",
                       "contain", "contains", "containing"}


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _build_alias_map(pairs):
    m = {}
    for key, aliases in pairs:
        for a in aliases:
            m[_norm(a)] = key
    return m


NUTRIENT_ALIASES = _build_alias_map((n.key, n.aliases) for n in schema.NUTRIENTS)
GOAL_ALIASES = _build_alias_map((g[0], g[3]) for g in GOALS)


def _extract_aliases(text: str, alias_map: dict[str, str]):
    """Find aliases (longest first, optional plural 's'), remove them from the text."""
    found: list[str] = []
    for alias in sorted(alias_map, key=len, reverse=True):
        pat = re.compile(rf"(?<![a-z0-9]){re.escape(alias)}(?:s|es)?(?![a-z0-9])")
        if pat.search(text):
            key = alias_map[alias]
            if key not in found:
                found.append(key)
            text = pat.sub(" ", text)
    return " ".join(text.split()), found


# ------------------------------------------------------------- food name matching
def _singular(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("oes"):
        return tok[:-2]
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def food_patterns(tokens: list[str]) -> list[str]:
    """One full-match regex per token: whole word, singular/plural tolerant.
    Used with Cypher `=~` against Food.name_lower; ALL patterns must match."""
    pats = []
    for tok in tokens:
        base = _singular(tok)
        variants = {tok, base, base + "s", base + "es"}
        if base.endswith("y"):
            variants.add(base[:-1] + "ies")
        alt = "|".join(sorted(re.escape(v) for v in variants))
        pats.append(rf".*\b(?:{alt})\b.*")
    return pats


# ------------------------------------------------------------------ Cypher
Q_FIND_FOODS = """
MATCH (f:Food)
WHERE ALL(p IN $patterns WHERE f.name_lower =~ p)
WITH f ORDER BY CASE f.data_type WHEN 'foundation_food' THEN 0 WHEN 'sr_legacy_food' THEN 1 ELSE 2 END,
                size(f.name), f.name
WITH collect(f) AS fs
RETURN size(fs) AS total,
       [x IN fs[0..$limit] | {fdc_id: x.fdc_id, name: x.name, data_type: x.data_type}] AS foods
"""

Q_FOOD_NUTRIENTS = """
MATCH (f:Food)-[r:CONTAINS]->(n:Nutrient)
WHERE f.fdc_id IN $fdc_ids
  AND ($keys IS NULL OR n.key IN $keys)
  AND ($include_zero OR r.amount > 0)
RETURN f.fdc_id AS fdc_id, f.name AS food, f.data_type AS data_type,
       n.name AS nutrient, n.key AS nutrient_key, r.amount AS amount, r.unit AS unit,
       r.basis AS basis, r.source AS source
ORDER BY f.fdc_id, n.sort_order
"""

Q_NUTRIENT_FOODS = """
MATCH (f:Food)-[r:CONTAINS]->(n:Nutrient {key: $key})
WHERE r.amount > 0
RETURN f.fdc_id AS fdc_id, f.name AS food, f.data_type AS data_type,
       n.name AS nutrient, n.key AS nutrient_key, r.amount AS amount, r.unit AS unit,
       r.basis AS basis, r.source AS source
ORDER BY r.amount DESC, f.name
LIMIT $limit
"""

Q_FOOD_CATEGORY = """
MATCH (f:Food)-[r:BELONGS_TO]->(c:FoodCategory)
WHERE f.fdc_id IN $fdc_ids
RETURN f.fdc_id AS fdc_id, f.name AS food, c.name AS category, r.category_source AS category_source
"""

Q_CATEGORY_NAMES = "MATCH (c:FoodCategory) RETURN c.name AS name"

Q_CATEGORY_FOODS = """
MATCH (f:Food)-[r:BELONGS_TO]->(c:FoodCategory {name: $name})
WITH c, r, f ORDER BY f.name
WITH c, collect({fdc_id: f.fdc_id, food: f.name, category_source: r.category_source}) AS fs
RETURN size(fs) AS total, c.name AS category, fs[0..$limit] AS foods
"""

Q_GOAL_NUTRIENTS = """
MATCH (n:Nutrient)-[s:SUPPORTS]->(g:Goal)
WHERE g.key IN $goal_keys
RETURN g.name AS goal, g.key AS goal_key, n.name AS nutrient, n.key AS nutrient_key,
       s.basis AS basis, s.curated AS curated, s.source AS curation_source
ORDER BY g.name, n.sort_order
"""

# Multi-hop: Goal <-SUPPORTS- Nutrient <-CONTAINS- Food, top foods PER nutrient
# (amounts of different nutrients are not comparable, so ranking is within a nutrient).
Q_GOAL_FOODS = """
MATCH (n:Nutrient)-[s:SUPPORTS]->(g:Goal)
WHERE g.key IN $goal_keys
MATCH (f:Food)-[r:CONTAINS]->(n)
WHERE r.amount > 0
WITH g, n, s, f, r ORDER BY r.amount DESC
WITH g, n, s, collect({fdc_id: f.fdc_id, food: f.name, amount: r.amount, unit: r.unit}) AS top
UNWIND top[0..$limit] AS t
RETURN g.name AS goal, g.key AS goal_key, n.name AS nutrient, n.key AS nutrient_key,
       t.food AS food, t.fdc_id AS fdc_id, t.amount AS amount, t.unit AS unit,
       s.basis AS basis, s.source AS curation_source
ORDER BY g.name, n.sort_order, t.amount DESC
"""


# ------------------------------------------------------------------ retriever
class GraphRetriever:
    """Holds one Neo4j driver. Create once, reuse (e.g. at FastAPI start-up)."""

    def __init__(self, driver=None, database: str | None = None):
        self._owns_driver = driver is None
        if driver is None:
            driver, settings = schema.get_driver()
            database = database or settings.database
        self._driver = driver
        self._database = database or "neo4j"
        self._category_cache: list[str] | None = None

    def close(self) -> None:
        if self._owns_driver:
            self._driver.close()

    # ---- data access (each is one Cypher query; overridden in offline tests) ----
    def _run(self, cypher: str, **params) -> list[dict]:
        records, _, _ = self._driver.execute_query(cypher, params, database_=self._database)
        return [r.data() for r in records]

    def category_names(self) -> list[str]:
        if self._category_cache is None:
            self._category_cache = [r["name"] for r in self._run(Q_CATEGORY_NAMES)]
        return self._category_cache

    def find_foods(self, tokens: list[str], limit: int):
        rows = self._run(Q_FIND_FOODS, patterns=food_patterns(tokens), limit=limit)
        return (rows[0]["total"], rows[0]["foods"]) if rows else (0, [])

    def food_nutrients(self, fdc_ids, nutrient_keys=None, include_zero=False):
        return self._run(Q_FOOD_NUTRIENTS, fdc_ids=list(fdc_ids), keys=nutrient_keys, include_zero=include_zero)

    def nutrient_foods(self, nutrient_key: str, limit: int):
        return self._run(Q_NUTRIENT_FOODS, key=nutrient_key, limit=limit)

    def food_categories(self, fdc_ids):
        return self._run(Q_FOOD_CATEGORY, fdc_ids=list(fdc_ids))

    def category_foods(self, category: str, limit: int):
        rows = self._run(Q_CATEGORY_FOODS, name=category, limit=limit)
        return (rows[0]["total"], rows[0]["foods"]) if rows else (0, [])

    def goal_nutrients(self, goal_keys):
        return self._run(Q_GOAL_NUTRIENTS, goal_keys=list(goal_keys))

    def goal_foods(self, goal_keys, per_nutrient_limit: int):
        return self._run(Q_GOAL_FOODS, goal_keys=list(goal_keys), limit=per_nutrient_limit)

    # ---- query understanding ----
    def _extract_category_names(self, text: str):
        found = []
        for name in sorted(self.category_names(), key=len, reverse=True):
            variants = {_norm(name)}
            if name.lower().endswith(" products"):
                variants.add(_norm(name[: -len(" products")]))
            for v in variants:
                pat = re.compile(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])")
                if v and pat.search(text):
                    found.append(name)
                    text = pat.sub(" ", text)
                    break
        return " ".join(text.split()), found

    # ---- public entry point ----
    def retrieve(self, query: str, *, max_foods: int = 3, limit: int = 10) -> dict:
        """max_foods: how many matching foods to expand for food questions.
        limit: max rows for ranked lists (nutrient->foods, category->foods, per-nutrient in goal->foods)."""
        out = {"query": query, "intent": "unknown", "confidence": "none",
               "entities": {"food_term": None, "foods": [], "nutrients": [], "goals": [], "categories": []},
               "results": [], "notes": []}
        if not isinstance(query, str) or not query.strip():
            out["notes"].append("Empty query.")
            return out

        text = _norm(query)
        text, goals = _extract_aliases(text, GOAL_ALIASES)
        text, nutrients = _extract_aliases(text, NUTRIENT_ALIASES)
        # Category names are only matched for explicit "foods in the X category" questions;
        # otherwise a category called e.g. "Salmon" would swallow the food word in
        # "what category does salmon belong to?".
        cats: list[str] = []
        if set(text.split()) & CATEGORY_WORDS and set(text.split()) & FOOD_WORDS:
            text, cats = self._extract_category_names(text)
        words = text.split()
        wordset = set(words)
        food_tokens = [w for w in words if w not in STOPWORDS and not w.isdigit()]
        food_term = " ".join(food_tokens) or None
        out["entities"].update(food_term=food_term, nutrients=nutrients, goals=goals, categories=cats)

        # ---- intent selection (first match wins) ----
        if goals:
            if wordset & FOOD_WORDS:
                return self._goal_foods(out, goals, limit)
            return self._goal_nutrients(out, goals)
        if nutrients:
            if food_tokens:
                return self._food_nutrients(out, food_tokens, nutrients, max_foods, "food_nutrient_amount")
            return self._nutrient_foods(out, nutrients, limit)
        if cats and not food_tokens:
            return self._category_foods(out, cats, limit)
        if food_tokens and wordset & CATEGORY_WORDS:
            return self._food_category(out, food_tokens, max_foods)
        if food_tokens and wordset & NUTRIENT_LIST_WORDS:
            return self._food_nutrients(out, food_tokens, None, max_foods, "food_nutrients")

        out["notes"].append("The question did not map to any supported graph query "
                            "(food->nutrients, nutrient->foods, food->category, goal->nutrients, goal->foods).")
        return out

    # ---- intent handlers ----
    def _resolve_foods(self, out, tokens, max_foods):
        total, foods = self.find_foods(tokens, max_foods)
        out["entities"]["foods"] = foods
        if total == 0:
            out["notes"].append(f"No food in the graph matches '{' '.join(tokens)}'.")
        elif total > len(foods):
            out["notes"].append(f"{total} foods match '{' '.join(tokens)}'; showing the best {len(foods)}.")
        return total, foods

    def _finish(self, out, total_matches=None, shown=None):
        if not out["results"]:
            out["confidence"] = "none"
        elif total_matches is not None and shown is not None and total_matches > shown:
            out["confidence"] = "low"
        else:
            out["confidence"] = "high"
        return out

    def _food_nutrients(self, out, tokens, nutrient_keys, max_foods, intent):
        out["intent"] = intent
        total, foods = self._resolve_foods(out, tokens, max_foods)
        if not foods:
            return out
        rows = self.food_nutrients([f["fdc_id"] for f in foods], nutrient_keys)
        order = {f["fdc_id"]: i for i, f in enumerate(foods)}
        rows.sort(key=lambda r: order[r["fdc_id"]])  # stable: keeps nutrient order within a food
        out["results"] = [{**r, "relationship": "CONTAINS"} for r in rows]
        if nutrient_keys and not rows:
            out["notes"].append("The matching foods have no recorded value for that nutrient.")
        return self._finish(out, total, len(foods))

    def _nutrient_foods(self, out, nutrient_keys, limit):
        out["intent"] = "nutrient_foods"
        for key in nutrient_keys:
            out["results"].extend({**r, "relationship": "CONTAINS"} for r in self.nutrient_foods(key, limit))
        out["notes"].append("Ranked by amount per 100 g across all USDA foods in the graph.")
        return self._finish(out)

    def _food_category(self, out, tokens, max_foods):
        out["intent"] = "food_category"
        total, foods = self._resolve_foods(out, tokens, max_foods)
        if not foods:
            return out
        rows = self.food_categories([f["fdc_id"] for f in foods])
        order = {f["fdc_id"]: i for i, f in enumerate(foods)}
        rows.sort(key=lambda r: order[r["fdc_id"]])
        out["results"] = [{**r, "relationship": "BELONGS_TO"} for r in rows]
        return self._finish(out, total, len(foods))

    def _category_foods(self, out, cats, limit):
        out["intent"] = "category_foods"
        for cat in cats:
            total, foods = self.category_foods(cat, limit)
            out["results"].extend({"category": cat, **f, "relationship": "BELONGS_TO"} for f in foods)
            if total > len(foods):
                out["notes"].append(f"'{cat}' has {total} foods; showing the first {len(foods)} alphabetically.")
        return self._finish(out)

    def _goal_nutrients(self, out, goals):
        out["intent"] = "goal_nutrients"
        rows = self.goal_nutrients(goals)
        out["results"] = [{**r, "relationship": "SUPPORTS"} for r in rows]
        out["notes"].append("Nutrient->goal links are manually curated, not USDA data.")
        return self._finish(out)

    def _goal_foods(self, out, goals, limit):
        out["intent"] = "goal_foods"
        per = max(1, min(limit, 5))
        rows = self.goal_foods(goals, per)
        out["results"] = [{**r, "relationship": "Food-CONTAINS->Nutrient-SUPPORTS->Goal"} for r in rows]
        out["notes"].append(f"Top {per} foods per supporting nutrient, ranked by amount per 100 g. "
                            "Nutrient->goal links are manually curated, not USDA data.")
        return self._finish(out)


# ------------------------------------------------------------------ helpers
def format_for_llm(result: dict, max_rows: int = 25) -> str:
    """Compact plain-text rendering of a result, for pasting into an LLM prompt
    next to the RAG context."""
    if not result["results"]:
        return ""
    lines = [f"[Knowledge graph | {result['intent']}]"]
    for r in result["results"][:max_rows]:
        rel = r.get("relationship")
        if rel == "SUPPORTS":
            lines.append(f"- {r['nutrient']} supports {r['goal']} (curated: {r['basis']})")
        elif rel == "BELONGS_TO" and "category" in r:
            lines.append(f"- {r.get('food', '')} belongs to category '{r['category']}'".replace("-  ", "- "))
        elif "goal" in r:
            lines.append(f"- {r['food']}: {r['amount']:g} {r['unit']} {r['nutrient']} per 100 g (supports {r['goal']})")
        else:
            lines.append(f"- {r['food']}: {r['amount']:g} {r['unit']} {r['nutrient']} per 100 g (USDA)")
    return "\n".join(lines)


_default: GraphRetriever | None = None


def retrieve_from_graph(query: str, **kwargs) -> dict:
    """Module-level convenience. Lazily opens one shared connection."""
    global _default
    if _default is None:
        _default = GraphRetriever()
    return _default.retrieve(query, **kwargs)


def close_graph() -> None:
    global _default
    if _default is not None:
        _default.close()
        _default = None


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What nutrients does salmon contain?"
    try:
        print(json.dumps(retrieve_from_graph(q), indent=2, ensure_ascii=False))
    finally:
        close_graph()
