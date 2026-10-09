import asyncio
import logging
import re

from .retriever import retrieve_foods
from .llm_client import generate_answer
from graph.graph_retriever import retrieve_from_graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
GRAPH_RETRIEVAL_TIMEOUT_SECONDS = 5
NUMBER_PATTERN = re.compile(r"(?<!\w)\d+(?:\.\d+)?(?!\w)")
RANGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\b")
UNSUPPORTED_BASIS_PATTERN = re.compile(
    r"\b(?:typical serving|per (?:the )?(?:listed )?serving|portion shown|whole foods?)\b",
    flags=re.IGNORECASE,
)


def _has_unsupported_numbers(answer, context):
    context_normalized = context.casefold()
    if any(
        phrase.casefold() not in context_normalized
        for phrase in UNSUPPORTED_BASIS_PATTERN.findall(answer)
    ):
        return True

    if any(match.group(0).casefold() not in context_normalized for match in RANGE_PATTERN.finditer(answer)):
        return True

    context_tokens = set(re.findall(r"[a-z0-9]+", context_normalized))
    for line in answer.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("*").strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0].casefold().startswith("food ("):
            continue
        food_tokens = re.findall(r"[a-z0-9]+", cells[0].casefold())
        if food_tokens and any(token not in context_tokens for token in food_tokens):
            return True

    context_numbers = NUMBER_PATTERN.findall(context)
    context_values = [float(number) for number in context_numbers]
    exact_numbers = set(context_numbers)

    for number in NUMBER_PATTERN.findall(answer):
        if number in exact_numbers:
            continue

        precision = len(number.partition(".")[2])
        value = float(number)
        if not any(round(context_value, precision) == value for context_value in context_values):
            return True

    return False


def _retrieved_facts_summary(results, graph_result):
    facts = []
    seen = set()

    def add_fact(food, value, unit, nutrient, basis=None):
        if food is None or value is None:
            return
        key = (str(food).strip().casefold(), str(value), str(unit).casefold(), str(nutrient).casefold())
        if key in seen:
            return
        seen.add(key)
        measurement = " ".join(part for part in (str(value), unit, nutrient) if part)
        if basis:
            measurement = f"{measurement} ({basis})"
        facts.append(f"{food}: {measurement}")

    for item in graph_result.get("results", []):
        add_fact(
            item.get("food"),
            item.get("amount"),
            item.get("unit"),
            item.get("nutrient"),
            item.get("basis"),
        )

    for item in results:
        nutrient = item.get("nutrient")
        document = item.get("document", "")
        unit_match = re.search(
            rf"^\s*{re.escape(str(nutrient))}\s*:\s*[-+]?\d*\.?\d+\s*(\S+)",
            document,
            flags=re.IGNORECASE | re.MULTILINE,
        ) if nutrient else None
        add_fact(
            item.get("food"),
            item.get("value"),
            unit_match.group(1) if unit_match else None,
            nutrient,
        )

    if not facts:
        return "The retrieved records do not provide enough detail to answer this question."
    return "The retrieved records report: " + "; ".join(facts) + "."


def build_context(results):
    context = []

    for i, result in enumerate(results, start=1):
        context.append(
            f"""
            Food {i}:
            {result["document"]}
            """
        )

    return "\n".join(context)


def _graph_sources(graph_result):
    grouped = {}
    for food in graph_result.get("entities", {}).get("foods", []):
        if food.get("name"):
            grouped[food.get("fdc_id") or str(food["name"]).strip().casefold()] = {
                "food_id": food.get("fdc_id"), "food_name": food["name"],
                "food_type": food.get("data_type"), "nutrition": {},
                "basis": "per 100 g", "source": "USDA FoodData Central",
            }
    for row in graph_result.get("results", []):
        food_id = row.get("fdc_id")
        name = row.get("food")
        if not name:
            continue
        key = food_id if food_id is not None else str(name).strip().casefold()
        source = grouped.setdefault(key, {
            "food_id": food_id,
            "food_name": name,
            "food_type": row.get("data_type"),
            "nutrition": {},
            "basis": row.get("basis") or "per 100 g",
            "source": row.get("source") or "USDA FoodData Central",
        })
        nutrient = row.get("nutrient_key") or row.get("nutrient")
        if nutrient and row.get("amount") is not None:
            source["nutrition"][nutrient] = row["amount"]
    for source in grouped.values():
        source["detail"] = "; ".join(
            f"{value:g} {next((r.get('unit', '') for r in graph_result.get('results', []) if r.get('food') == source['food_name'] and (r.get('nutrient_key') or r.get('nutrient')) == key), '')} {key.replace('_', ' ')}"
            for key, value in source["nutrition"].items()
        )
        if source["basis"]:
            source["detail"] = f"{source['detail']} ({source['basis']})" if source["detail"] else source["basis"]
    return list(grouped.values())


def _structured_answer(graph_result):
    """Render database-backed quantitative intents without asking the LLM to do arithmetic."""
    intent = graph_result.get("intent")
    rows = graph_result.get("results", [])
    if intent == "food_comparison":
        foods = graph_result.get("entities", {}).get("foods", [])
        if len(foods) < 2:
            return "I couldn't reliably match at least two foods in the USDA records. Please clarify the food names."
        by_key = {}
        for row in rows:
            by_key.setdefault(row.get("nutrient_key"), {})[row.get("fdc_id")] = row
        sections = []
        for nutrient_key in graph_result.get("entities", {}).get("nutrients", []):
            nutrient_rows = by_key.get(nutrient_key, {})
            sample = next((r for r in nutrient_rows.values() if r), {})
            label = sample.get("nutrient") or nutrient_key.replace("_", " ").title()
            unit = sample.get("unit", "")
            values = [nutrient_rows.get(food.get("fdc_id")) for food in foods]
            sections.append(f"**{label} comparison (per 100 g)**\n\n| Food | {label} |\n| --- | ---: |\n" + "\n".join(
                f"| {food['name']} | {row['amount']:g} {row.get('unit', unit)} |" if row else f"| {food['name']} | Not available |"
                for food, row in zip(foods, values)
            ))
            present = [(food, row) for food, row in zip(foods, values) if row is not None]
            if len(present) >= 2:
                low, high = min(present, key=lambda pair: pair[1]["amount"]), max(present, key=lambda pair: pair[1]["amount"])
                difference = high[1]["amount"] - low[1]["amount"]
                pct = (difference / low[1]["amount"] * 100) if low[1]["amount"] else None
                if difference == 0:
                    conclusion = f"**Result:** Both foods have the same recorded {label.lower()} value per 100 g."
                else:
                    conclusion = f"**Result:** {high[0]['name']} has {difference:g} {unit} more {label.lower()} per 100 g"
                    if pct is not None:
                        conclusion += f" ({pct:.1f}% more than {low[0]['name']})."
                    else:
                        conclusion += " (percentage difference is undefined because the lower value is zero)."
                sections.append(conclusion)
        if not sections:
            return "The matched foods do not have recorded values for the requested comparison."
        states = {}
        for food in foods:
            match = re.search(r"\b(raw|cooked|boiled|roasted|baked|fried|dried)\b", food["name"], re.I)
            states[food["name"]] = match.group(1).lower() if match else "unspecified"
        state_note = ""
        if len(set(states.values())) > 1:
            state_note = " Preparation labels differ or are unspecified: " + ", ".join(f"{name} ({state})" for name, state in states.items()) + "."
        prep = "Food descriptions retain USDA preparation labels; values are not adjusted across forms." + state_note
        ambiguity_notes = [note for note in graph_result.get("notes", []) if "matches multiple" in note]
        if ambiguity_notes:
            prep += " " + " ".join(ambiguity_notes)
        sections.append(f"**Data note:** Values are USDA records per 100 g. {prep}")
        return "\n\n".join(sections)

    if intent in {"food_nutrients", "food_nutrient_amount", "nutrient_foods"} and rows:
        sections = []
        nutrients = graph_result.get("entities", {}).get("nutrients", [])
        if not nutrients:
            nutrients = list(dict.fromkeys(r.get("nutrient_key") for r in rows if r.get("nutrient_key")))
        for nutrient in nutrients:
            nutrient_rows = [r for r in rows if r.get("nutrient_key") == nutrient]
            if not nutrient_rows:
                continue
            label = nutrient_rows[0].get("nutrient", nutrient.title())
            title = f"Foods ranked by {label.lower()} per 100 g" if intent == "nutrient_foods" else f"{label} in the matched food records (per 100 g)"
            sections.append(f"**{title}**\n\n| Food | {label} |\n| --- | ---: |\n" + "\n".join(
                f"| {r['food']} | {r['amount']:g} {r['unit']} |" for r in nutrient_rows
            ))
            if intent == "nutrient_foods":
                sections[-1] += f"\n\nShowing {len(nutrient_rows)} records, sorted by {label.lower()} amount per 100 g."
        if sections:
            sections.append("**Data note:** Values are USDA records per 100 g. A concentration ranking is not a serving-size ranking." if intent == "nutrient_foods" else "**Data note:** USDA values are per 100 g; zero is a recorded value and omitted foods have unavailable measurements.")
            if intent == "food_nutrient_amount" and re.search(r"\b(serving|portion|one|\d+\s*(?:g|gram))\b", graph_result.get("query", ""), re.I):
                sections.append("No matching gram-weight portion data is available, so the result is reported per 100 g.")
            return "\n\n".join(sections)
    return None


async def answer_question(question):
    print("RAG: starting retrieval", flush=True)
    logger.info("RAG retrieval started")
    results = await asyncio.to_thread(retrieve_foods, question)

    print(f"RAG: Chroma retrieval completed ({len(results)} results)", flush=True)
    logger.info("Chroma retrieval completed; retrieved %d results", len(results))

    try:
        graph_result = await asyncio.wait_for(
            asyncio.to_thread(retrieve_from_graph, question),
            timeout=GRAPH_RETRIEVAL_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.exception("Neo4j retrieval failed; continuing with ChromaDB only")
        graph_result = {"intent": "unknown", "results": [], "notes": ["Knowledge graph unavailable."]}

    print("RAG: Neo4j retrieval completed", flush=True)
    logger.info("Neo4j graph retrieval completed")

    chroma_context = build_context(results)

    graph_context = ""
    if graph_result.get("results"):
        graph_context = "\n".join(
            str(item)
            for item in graph_result["results"]
        )

    context = f"""
    VECTOR DATABASE RESULTS:
    {chroma_context}

    KNOWLEDGE GRAPH RESULTS:
    {graph_context}
    """

    print("RAG: combined Chroma + Neo4j context built", flush=True)
    logger.info("Combined vector and graph context built")

    structured_answer = _structured_answer(graph_result)
    if structured_answer is not None:
        answer = structured_answer
    elif graph_result.get("intent") == "general_explanation":
        answer = "The available USDA records contain food nutrient measurements, but not enough evidence to explain this general nutrition concept reliably."
    elif graph_result.get("confidence") == "none" and not results:
        answer = "I couldn't find nutrition records that reliably answer this question. Try a specific food or nutrient."
    else:
        prompt = f"""
        You are Nutrix, an AI nutrition information assistant.

        Answer the user's question using ONLY the nutrition data
        provided in the context below.

        Rules:
        - Do not invent nutrition values.
        - Do not use nutrition facts that are not present in the context.
        - State only food and nutrient facts directly supported by a retrieved record.
        - Do not add general nutrition knowledge or combine values from different foods.
        - If the available data is insufficient, clearly say so.
        - Keep the answer concise and easy to understand.
        - Mention relevant food names and nutrition values when appropriate.
        - This is general nutrition information, not medical diagnosis or treatment.

        User question:
        {question}

        Retrieved nutrition data:
        {context}
        """
        print("RAG: calling Groq", flush=True)
        logger.info("Groq request started")
        answer = await generate_answer(prompt)
        if _has_unsupported_numbers(answer, context):
            logger.warning("LLM answer included values outside retrieved context; using retrieved facts")
            answer = _retrieved_facts_summary(results, graph_result)
        print("RAG: Groq returned", flush=True)
        logger.info("Groq request completed")

    return {
    "question": question,
    "answer": answer,
    "sources": _graph_sources(graph_result) if graph_result.get("results") or graph_result.get("intent") not in (None, "unknown") else [
        {
            "food_id": None,
            "food_name": result["food"],
            "food_type": None,
            "nutrition": {
                result["nutrient"]: result["value"]
            },
            "document": result["document"],
        }
        for result in results
    ],
    "graph_context": graph_result,
    "retrieval_metadata": {
        "retrieval_method": "chromadb",
        "top_k": len(results),
        "nutrient": results[0]["nutrient"] if results else None
    }
}
