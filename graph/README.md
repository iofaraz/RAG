# Nutrition Knowledge Graph (Member 1)

Neo4j knowledge graph built from the cleaned USDA dataset, plus a retriever that
returns structured, JSON-serialisable results. Independent of the RAG module,
FastAPI and Gemini.

## 1. Why a knowledge graph?

Vector search (the existing RAG) finds foods whose *text* resembles the question.
It is weak at **multi-hop** questions whose answer is spread over several facts:

> "Which foods contain nutrients that support bone health?"

That needs `Food → Nutrient → Goal`. A graph stores those links explicitly, so the
answer is a traversal, not a guess - and every number can be traced to its source.

## 2. Schema

```
 (Food)-[:CONTAINS {amount, unit, basis, source}]->(Nutrient)-[:SUPPORTS {basis, curated, source}]->(Goal)
   |
   +-[:BELONGS_TO {category_source}]->(FoodCategory)
```

| Node | Key | Properties | Count |
|---|---|---|---|
| `Food` | `fdc_id` (unique) | `name`, `name_lower`, `data_type`, `source` | 13,694 |
| `Nutrient` | `key` (unique) | `name`, `unit`, `csv_column`, `sort_order` | 25 |
| `FoodCategory` | `name` (unique) | - | depends on category source |
| `Goal` | `key` (unique) | `name`, `description` | 6 |

`Food → Goal` is **not stored**. It is derived by traversing through `Nutrient`,
so adding one `SUPPORTS` link automatically updates every food's goals.

Amounts are **per 100 g** (`basis` on each `CONTAINS`). A nutrient with no value in
the CSV gets **no relationship**. A real `0` is kept (USDA saying "0" is
information; "unknown" is not) and the retriever hides zeros by default.

## 3. What is USDA data and what is curated

| Layer | Relationships | Origin |
|---|---|---|
| USDA-derived | `Food-CONTAINS->Nutrient` (amount, unit) | `food_nutrition_clean.csv` |
| USDA-derived | `Food-BELONGS_TO->FoodCategory` | raw USDA tables; falls back to a name heuristic, labelled in `category_source` |
| **Curated** | `Nutrient-SUPPORTS->Goal` | `seed_knowledge.py`, written by hand |

Curated links carry `curated: true` and `source: "manual_curation"`. They are
small, role-descriptive, and deliberately conservative (e.g. "Calcium is a major
structural component of bone"). **Have the team read the `basis` sentences in
`seed_knowledge.py` before presenting and delete any you can't defend.**

### Where categories come from
The CSV has no category column. `category_resolver.py` tries, in order:
`usda_food_category` (food.csv + food_category.csv) → `usda_wweia`
(survey_fndds_food.csv + wweia_food_category.csv) → `derived_name_prefix`
(first comma chunk of the name: "Fish, salmon, raw" → "Fish"; a heuristic).
Run `python -m graph.graph_builder --inspect-categories` to see the coverage
you actually get **before** building.

## 4. Setup

```bash
pip install -r graph/requirements.txt
```

Neo4j 5.x, any of: Neo4j Desktop, Aura Free, or Docker:

```bash
docker run --name neo4j-food -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/choose-a-password neo4j:5
```

Configure (env vars or a `.env` file in the project root):

```
NEO4J_URI=bolt://localhost:7687      # default
NEO4J_USER=neo4j                     # default
NEO4J_PASSWORD=choose-a-password     # required
NEO4J_DATABASE=neo4j                 # default
```

## 5. Build the graph

Run from the **project root** (so `graph` is importable):

```bash
python -m graph.graph_builder --inspect-categories   # optional, no Neo4j needed
python -m graph.graph_builder                        # build; safe to re-run
python -m graph.graph_builder --reset                # wipe the 4 labels, then rebuild
```

Every write is a `MERGE` on a uniquely-constrained key, so re-running never
duplicates anything. Use `--reset` if the CSV changed in a way that *removes* data.
Raw USDA files and ChromaDB are never touched (read-only).

## 6. Retrieve

```python
from graph.graph_retriever import retrieve_from_graph

retrieve_from_graph("What nutrients does salmon contain?")
```
```json
{
  "query": "What nutrients does salmon contain?",
  "intent": "food_nutrients",
  "confidence": "low",
  "entities": {"food_term": "salmon", "foods": [{"fdc_id": 0, "name": "Fish, salmon, ..."}], "nutrients": [], "goals": [], "categories": []},
  "results": [
    {"fdc_id": 0, "food": "Fish, salmon, ...", "nutrient": "Protein", "nutrient_key": "protein",
     "amount": 22.3, "unit": "g", "basis": "per 100 g", "source": "USDA FoodData Central",
     "relationship": "CONTAINS"}
  ],
  "notes": ["65 foods match 'salmon'; showing the best 3."]
}
```
(`fdc_id` and values above are illustrative.)

| Question type | Example | `intent` |
|---|---|---|
| Food → nutrients | "What nutrients does salmon contain?" | `food_nutrients` |
| Food → one nutrient | "How much protein does salmon contain?" | `food_nutrient_amount` |
| Nutrient → foods | "What foods contain protein?" | `nutrient_foods` |
| Food → category | "What category does salmon belong to?" | `food_category` |
| Category → foods | "What foods are in the Fish category?" | `category_foods` |
| Goal → nutrients | "What nutrients are associated with bone health?" | `goal_nutrients` |
| **Food → Nutrient → Goal** | "What foods contain nutrients associated with bone health?" | `goal_foods` |

`confidence`: `high` = understood and fully resolved; `low` = answered, but the
food phrase matched many foods so only the best few were used; `none` = nothing
could be grounded in the graph, `results == []`. **Unknown questions never
produce fabricated results.**

Options: `retrieve_from_graph(q, max_foods=3, limit=10)`. For a long-lived service
create one `GraphRetriever()` at start-up and call `.retrieve(q)`; call
`close_graph()` / `.close()` on shutdown. `format_for_llm(result)` renders a
result as compact text for a prompt.

CLI: `python -m graph.graph_retriever "What foods contain protein?"`

Query understanding is deliberately simple (alias matching + stop-word removal).
It will not understand paraphrases like "grilled salmon" if "grilled" is not in
the USDA name. That is what the RAG side is for.

## 7. Example Cypher (paste into Neo4j Browser, http://localhost:7474)

```cypher
// Food -> nutrients
MATCH (f:Food)-[r:CONTAINS]->(n:Nutrient)
WHERE f.name_lower CONTAINS 'salmon, atlantic, wild, raw'
RETURN f.name, n.name, r.amount, r.unit ORDER BY n.sort_order;

// Nutrient -> top foods
MATCH (f:Food)-[r:CONTAINS]->(:Nutrient {key:'protein'})
RETURN f.name, r.amount, r.unit ORDER BY r.amount DESC LIMIT 10;

// Goal -> nutrients (curated)
MATCH (n:Nutrient)-[s:SUPPORTS]->(:Goal {key:'bone_health'})
RETURN n.name, s.basis;

// Multi-hop: Food -> Nutrient -> Goal
MATCH (f:Food)-[r:CONTAINS]->(n:Nutrient)-[:SUPPORTS]->(g:Goal {key:'bone_health'})
WHERE r.amount > 0
RETURN f.name, n.name, r.amount, r.unit ORDER BY r.amount DESC LIMIT 20;

// For the demo (visual): a few salmon foods, their nutrients, and the goals those support
MATCH p = (f:Food)-[:CONTAINS]->(n:Nutrient)-[:SUPPORTS]->(g:Goal)
WHERE f.name_lower CONTAINS 'salmon, atlantic, wild, raw'
RETURN p LIMIT 25;

// Which relationships are curated?
MATCH ()-[r]->() WHERE r.curated = true RETURN type(r), count(r);
```

## 8. Tests

```bash
pytest graph/tests -v
```
* `test_offline.py` - no Neo4j needed. Checks the nutrient mapping against the real
  CSV (every column mapped, units correct, NaN → no row, no duplicate rows), the
  category resolver, and the retriever's parsing/routing for all question types
  and for unknown/garbage queries, using a pandas stand-in for the Cypher calls.
* `test_integration.py` - needs a real Neo4j (skipped otherwise). Builds the graph,
  rebuilds it and asserts identical counts (no duplicates), checks missing values,
  amount/unit preservation, USDA/curated separation, and the 5 query types.
  It writes to the configured database (MERGE only) - use a dev database.

Set `GRAPH_TEST_CSV=/path/to/food_nutrition_clean.csv` to test against another CSV.

## 9. Integration with RAG (planned)

```
                    User question
                          |
                     FastAPI  (Member N)
                          |
              +-----------+------------+
              |                        |
     rag/nutrition_retriever    graph/graph_retriever
     (Chroma, fuzzy text)       (Neo4j, exact + multi-hop)
              |                        |
              +-----------+------------+
                          |
                  combined context
                          |
                    Gemini Flash
                          |
                       Answer
```

```python
from graph.graph_retriever import GraphRetriever, format_for_llm

graph = GraphRetriever()                      # once, at start-up

def build_context(question: str, rag_hits: list[str]) -> str:
    g = graph.retrieve(question)
    parts = ["Vector search results:\n" + "\n".join(rag_hits)]
    if g["confidence"] != "none":
        parts.append(format_for_llm(g))       # only when the graph actually has something
    return "\n\n".join(parts)
```

When `confidence == "none"` the graph contributes nothing and RAG answers alone.
Graph rows with `curated: true` / `SUPPORTS` are general-nutrition statements, not
USDA measurements - the prompt should keep that distinction.

## 10. Known limitations
* Rankings are by raw amount per 100 g over all 13,694 records, so ingredients
  and supplements (baking powder for calcium, soy protein isolate, cod-liver oil)
  rank above everyday foods. This is what the data says; filtering by category
  (once real USDA categories are loaded) is the natural next improvement.
* Ambiguous food names ("salmon" → 65 foods) use the best few matches, preferring
  Foundation, then SR Legacy, then FNDDS, then shorter names; `confidence: "low"` flags it.
* Category names are only matched for explicit "foods in the X category" questions.
