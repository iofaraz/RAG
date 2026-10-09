const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const NUTRIENT_KEYS = {
  calories: "calories_kcal", protein: "protein_g", carbohydrates: "carbs_g",
  fat: "fat_g", fiber: "fiber_g", sodium: "sodium_mg", calcium: "calcium_mg",
  iron: "iron_mg", vitamin_c: "vitamin_c_mg",
};

/** Send a nutrition question to the FastAPI backend. */
export async function askQuestion(question) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question }),
    });
  } catch {
    throw new Error("The nutrition service is unavailable. Check your connection and try again.");
  }

  if (!response.ok) {
    if (response.status >= 500) {
      throw new Error("The nutrition service is temporarily unavailable. Please try again shortly.");
    }

    throw new Error("We couldn't process that question. Please check it and try again.");
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The nutrition service returned an invalid response. Please try again.");
  }

  return {
    question: data.query ?? question,
    answer: typeof data.answer === "string" ? data.answer : "",
    sources: Array.isArray(data.sources)
      ? data.sources.map((source, index) => ({
          food_id: source.food_id ?? `${source.name ?? "source"}-${index}`,
          food_name: source.name ?? "Nutrition source",
          food_type: source.food_type ?? null,
          nutrition: Object.fromEntries(Object.entries(source.nutrition ?? {}).map(([key, value]) => [NUTRIENT_KEYS[key] ?? key, value])),
          detail: source.detail ?? null,
          score: source.score ?? null,
          basis: source.basis ?? null,
          source: source.source ?? null,
        }))
      : [],
    warnings: Array.isArray(data.warnings) ? data.warnings : [],
  };
}
